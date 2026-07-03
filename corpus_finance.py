# -*- coding: utf-8 -*-
"""
CORPUS FINANCIER D'ENTREPRISE (simulé) — Agent Hybride Finance V1
=================================================================
Documents fictifs mais réalistes d'une entreprise :
politique d'achats, procédure TVA, normes comptables, registre des
fournisseurs et contrats, journal des factures, politique anti-fraude.

Aucune donnée réelle. Tout est simulé à but pédagogique.
Des ANOMALIES sont volontairement insérées dans le journal des factures
pour que l'agent puisse les détecter (doublon, fractionnement, TVA,
fournisseur offshore, auto-validation, dépassement de plafond).

Cas d'usage multi-hop visé :
    Facture -> Fournisseur -> Contrat -> Projet -> Département -> Responsable
"""

# ---------------------------------------------------------------------------
# LE CORPUS : 6 documents financiers simulés
# (générés aussi en PDF par generer_pdfs.py pour le RAG vectoriel)
# ---------------------------------------------------------------------------
CORPUS = """
DOC 1 — POLITIQUE D'ACHATS INTERNE :
Tout achat supérieur à 10 000 EUR exige trois devis comparatifs. Tout achat
supérieur à 50 000 EUR exige la validation du Directeur Administratif et
Financier (DAF). Tout achat supérieur à 100 000 EUR exige la validation du
Comité des Engagements. Les frais de restauration sont plafonnés à 150 EUR
par personne. Les achats informatiques ne sont autorisés qu'auprès de
fournisseurs agréés inscrits au registre. Le fractionnement d'une commande
en plusieurs factures pour contourner les seuils d'approbation est
strictement interdit.

DOC 2 — PROCÉDURE TVA :
Le taux normal de TVA est de 20 %. Le taux réduit de 10 % s'applique à la
restauration et à l'hôtellerie. Le taux de 7 % s'applique aux fournitures
scolaires. La TVA n'est déductible que si la facture est conforme : numéro
de facture, identifiant fiscal (ICE) du fournisseur, date et désignation.
La TVA sur les véhicules de tourisme n'est pas déductible. La déclaration
de TVA est mensuelle et doit être déposée avant le 20 du mois suivant.
Appliquer un taux de TVA incorrect constitue une anomalie fiscale à signaler.

DOC 3 — NORMES COMPTABLES INTERNES :
Chaque facture est imputée sur un compte de charge unique et rattachée à un
centre de coût. Il est interdit d'enregistrer deux fois la même facture
(doublon comptable). Toute écriture supérieure à 20 000 EUR doit être
justifiée par une pièce originale. Le rapprochement bancaire est mensuel.
Séparation des tâches obligatoire : le demandeur d'un achat ne peut jamais
être son propre valideur. Les comptes 61xx couvrent les charges externes,
le compte 6226 les honoraires, le compte 6135 la location de matériel.

DOC 4 — REGISTRE DES FOURNISSEURS ET CONTRATS :
TechnoSupply SARL est un fournisseur agréé, lié par le contrat CT-2024-011
au projet Ambre, géré par le département IT dirigé par Karim Alaoui.
MegaConsulting Ltd est domicilié offshore (Belize), N'EST PAS agréé, n'a
aucun contrat actif et est signalé à risque élevé par la conformité.
BuroPlus est un fournisseur agréé (contrat CT-2023-045, fournitures de
bureau, centre de coût CC-ADMIN). AtlasVoyages est agréé (contrat
CT-2024-020, frais de mission) et rattaché au projet Horizon, dirigé par
Rim Elmers au sein du département Finance, dont la responsable est
Sara Benali.

DOC 5 — JOURNAL DES FACTURES (extrait T1 2026) :
FAC-2026-101 : TechnoSupply, 45 000 EUR HT, TVA 20 %, projet Ambre,
compte 6135, centre de coût CC-IT, validée par le DAF — conforme.
FAC-2026-102 : MegaConsulting, 120 000 EUR HT, TVA 20 %, objet « conseil
stratégique », sans contrat ni bon de commande, compte 6226, centre de coût
CC-DIR, demandée ET validée par Omar Chraibi.
FAC-2026-117 : MegaConsulting, 120 000 EUR HT, même objet et même date que
la facture FAC-2026-102 — doublon présumé.
FAC-2026-125 : AtlasVoyages, 9 800 EUR, mission Casablanca, suivie le même
jour de FAC-2026-126 : AtlasVoyages, 9 900 EUR, même mission — suspicion de
fractionnement pour rester sous le seuil des 10 000 EUR.
FAC-2026-130 : BuroPlus, 3 200 EUR de fournitures de bureau avec TVA
appliquée à 10 % au lieu du taux normal de 20 % — anomalie TVA.
FAC-2026-133 : restaurant La Corniche, repas d'affaires facturé 480 EUR
par personne, au-delà du plafond de 150 EUR par personne.

DOC 6 — POLITIQUE ANTI-FRAUDE ET CONFORMITÉ :
Signaux d'alerte fraude : factures en doublon, fournisseur offshore non
agréé, fractionnement de commandes, auto-validation (demandeur = valideur),
montants ronds répétés, fournisseur sans contrat. Tout dossier présentant
un score de risque supérieur à 70, une fraude suspectée ou un montant
supérieur à 100 000 EUR doit être transmis à un contrôleur humain avant
toute décision. L'entreprise est soumise à la loi 43-05 relative à la lutte
contre le blanchiment de capitaux. Les pièces comptables sont conservées
10 ans. Les données personnelles des employés sont protégées par la
loi 09-08 : jamais de salaire nominatif ni de RIB dans les rapports.
"""


# ---------------------------------------------------------------------------
# PROMPT D'EXTRACTION adapté au domaine financier
# ---------------------------------------------------------------------------
PROMPT_EXTRACTION = """Tu es un expert en extraction de connaissances financières et comptables
(Knowledge Graph d'audit). À partir des documents ci-dessous, extrais toutes les
entités et toutes les relations utiles pour détecter des anomalies financières.

Types d'entités : Entreprise, Facture, Fournisseur, Employe, CompteComptable,
Transaction, CentreCout, Projet, Contrat, Departement, Politique, Regle, Taux.

Réponds UNIQUEMENT avec un tableau JSON de triplets, au format :
[
  {{"source": "FAC-2026-102", "type_source": "Facture",
    "relation": "EMISE_PAR", "cible": "MegaConsulting", "type_cible": "Fournisseur",
    "source_doc": "DOC 5"}}
]

Relations autorisées (MAJUSCULES) :
- EMISE_PAR         (une facture -> un fournisseur)
- LIEE_AU_CONTRAT   (un fournisseur/facture -> un contrat)
- RATTACHEE_AU_PROJET (une facture/contrat -> un projet)
- GERE_PAR          (un projet -> un département)
- DIRIGE            (une personne -> un département/projet)
- IMPUTEE_SUR       (une facture -> un compte comptable)
- AFFECTEE_AU_CENTRE (une facture -> un centre de coût)
- VALIDEE_PAR       (une facture -> un employé)
- DEMANDEE_PAR      (une facture -> un employé)
- DOUBLON_DE        (une facture -> une autre facture)
- VIOLE             (une facture/pratique -> une règle ou politique)
- A_RISQUE          (un fournisseur -> un motif de risque)
- SOUMISE_A_TVA     (une opération -> un taux de TVA)
- PLAFONNE_A        (une dépense -> un plafond)
- EXIGE             (un seuil/une règle -> une validation)

Règles :
- Une entrée par relation trouvée. Ajoute "source_doc" (DOC 1..6) pour la traçabilité.
- Normalise les noms d'entités (ex. "la facture FAC-2026-102" -> "FAC-2026-102").
- Pas de texte hors du JSON.

Documents :
{corpus}"""


# ---------------------------------------------------------------------------
# JEUX DE QUESTIONS
# ---------------------------------------------------------------------------
# 5 questions "légitimes" pour le comparatif vecteur vs graphe
QUESTIONS_COMPARATIF = [
    ("Factuelle simple",
     "Quel est le taux normal de TVA et quel taux a été appliqué sur la facture FAC-2026-130 ?"),
    ("Doublon",
     "Existe-t-il des factures en doublon dans le journal du T1 2026 ?"),
    ("Multi-hop (4 sauts)",
     "La facture FAC-2026-102 est-elle conforme ? Remonte au fournisseur, à son contrat, "
     "au projet et au valideur pour justifier ta réponse."),
    ("Politique interne",
     "Les factures AtlasVoyages FAC-2026-125 et FAC-2026-126 respectent-elles la politique d'achats ?"),
    ("Piège (info absente)",
     "Quel est le chiffre d'affaires de TechnoSupply en 2025 ?"),
]
