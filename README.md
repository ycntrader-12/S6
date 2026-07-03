# Agent Finance Hybride V1 — Détection de fraude & anomalies financières

Agent IA **hybride (RAG vectoriel + Knowledge Graph)** qui analyse un dossier
financier d'entreprise et détecte : incohérences comptables, risques de fraude,
anomalies de TVA, doublons de factures, dépenses hors politique interne,
fournisseurs à risque, transactions inhabituelles et violations réglementaires.

Il produit **toujours** une sortie **JSON valide à 100 %** contenant l'analyse,
un score de risque, les preuves, les sources (graphe + documents) et les
recommandations, sous le contrôle d'un circuit **Human-In-The-Loop** et de
**policies de sécurité** complètes.

> Réalisé dans le cadre de la Formation GenAI — ABA Technology.
> Réutilise l'architecture GraphRAG du lab précédent (mêmes types de nœuds,
> mêmes connexions, même schéma) ; seule la logique métier est passée au domaine Finance.
> Nouvelles collections Astra dédiées : `triplets_finance` et `chunks_finance`
> (les collections des labs précédents ne sont pas touchées).

---

## 1. Présentation

L'agent reçoit un « dossier » (question / description d'une ou plusieurs factures)
et l'analyse via un pipeline **multi-agents** LangGraph :

| Étape | Agent | Rôle |
|---|---|---|
| 1 | **Coordinateur** | Sécurité d'entrée + ouverture de la trace |
| 2 | **Vector Search** | Recherche RAG vectoriel (politiques, procédures, normes — Astra vectorize) |
| 3 | **Graph Search** | Traversée **multi-hop** du Knowledge Graph (Facture→Fournisseur→Contrat→Projet→Département→Responsable) |
| 4 | **Fusion** | Fusionne les deux contextes |
| 5 | **Expert Comptable** | Doublons, imputation, séparation des tâches |
| 6 | **Expert TVA** | Taux incorrects, TVA non déductible, factures non conformes |
| 7 | **Expert Fraude** | Fractionnement, offshore, auto-validation, doublons |
| 8 | **Expert Conformité** | Plafonds, seuils, loi 43-05 / 09-08 |
| 9 | **Score de Risque** | Agrégation pondérée des 4 experts |
| 10 | **Human-In-The-Loop** | Validation humaine si risque > 70, fraude, montant > 100 000 €, confiance < 80 % |
| 11 | **Rapport Final JSON** | Assemblage + garde de sortie + validation du schéma |

## 2. Architecture

```
Dossier ─▶ Coordinateur ─(bloqué)─────────────────────────▶ Refus JSON
               │
               └(autorisé)▶ Vector Search ▶ Graph Search ▶ Fusion
                                                              │
   Expert Comptable ◀─────────────────────────────────────────┘
        └▶ Expert TVA ▶ Expert Fraude ▶ Expert Conformité ▶ Score de Risque
                                                              │
                          ┌─(HITL requis)─▶ HITL ─(rejeté)─▶ Refus JSON
                          │                  └(approuvé/corrigé)─┐
                          └─(sinon)──────────────────────────────┴▶ Rapport Final JSON
```

Voir les diagrammes détaillés dans [`diagrammes.md`](diagrammes.md)
(flowchart, séquence, architecture, knowledge graph).

**Deux sources de connaissance :**
- **Vector RAG** → `chunks_finance` (Astra vectorize, embeddings NVIDIA `NV-Embed-QA`) :
  politiques internes, procédures, normes comptables, documentation PDF, contrats.
- **Knowledge Graph** → `triplets_finance` (Astra) : relations
  Entreprise / Facture / Fournisseur / Employé / Compte / Transaction / Centre de coût / Projet,
  parcourues en **multi-hop**.

## 3. Installation

```bash
cd finance-fraude-agent
python -m venv .venv
# Windows : .venv\Scripts\activate    |   Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configuration & variables d'environnement

Fichier `.env` (déjà présent) :

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Clé Groq (LLM `llama-3.3-70b-versatile`) |
| `ASTRA_DB_API_ENDPOINT` | Endpoint de la base Astra |
| `ASTRA_DB_APPLICATION_TOKEN` | Token applicatif Astra |

Collections utilisées : **`triplets_finance`** (graphe) et **`chunks_finance`** (vecteur),
créées automatiquement à l'indexation.

## 5. Exécution

```bash
# 1) Indexer le corpus : extrait les triplets + vectorise (crée les 2 collections Astra)
python agent_financier.py index

# 2) Analyser un dossier -> JSON (mode HITL console)
python agent_financier.py ask "Analyse la facture FAC-2026-102 de MegaConsulting"

# 3) Afficher le Knowledge Graph stocké
python agent_financier.py graph

# 4) Démo : 4 scénarios (fraude, injection, PII, facture conforme)
python agent_financier.py demo

# Générer les PDF du corpus (documentation source du RAG)
python generer_pdfs.py

# Campagne Red Team (attaque l'agent et vérifie ses défenses)
python redteam.py
```

> Sous Windows PowerShell, si la console coupe les accents/emoji :
> `` $env:PYTHONIOENCODING='utf-8' `` avant de lancer.

## 6. Déploiement

L'agent tourne en local (LangGraph + Astra managé). Pour un déploiement :
1. Provisionner la base Astra et générer un token (droits R/W sur les 2 collections).
2. Déposer `.env` via un secret manager (jamais en clair dans le dépôt).
3. `pip install -r requirements.txt` dans l'environnement cible.
4. Lancer `python agent_financier.py index` une fois, puis exposer `interroger()`
   derrière une API (FastAPI) avec authentification + RBAC (voir `securite.py`).

Le **workflow Langflow** `Indexation-GraphRAG-Finance.json` est **immédiatement
importable** dans la plateforme (mêmes nœuds/connexions que le workflow de référence,
table `triplets_finance`).

## 7. Structure du projet

```
finance-fraude-agent/
├─ .env                              # secrets (Groq + Astra)
├─ requirements.txt
├─ corpus_finance.py                 # corpus (6 docs) + prompt d'extraction + questions
├─ securite.py                       # policies : injection, PII, secrets, RBAC, rate-limit, audit…
├─ agent_financier.py                # l'agent hybride multi-agents (LangGraph) + traçabilité
├─ redteam.py                        # campagne Red Team (15 attaques OWASP LLM)
├─ generer_pdfs.py                   # génère docs_pdf/*.pdf (source du RAG vectoriel)
├─ _build_workflow.py                # construit le workflow JSON depuis la référence
├─ Indexation-GraphRAG-Finance.json  # workflow importable (Langflow)
├─ docs_pdf/                         # 6 PDF du corpus financier
├─ triplets_finance.json             # copie locale du Knowledge Graph
├─ audit_log.jsonl                   # journal d'audit (traçabilité)
├─ redteam_resultats.{md,json}       # résultats Red Team
└─ docs :
   ├─ README.md
   ├─ THREAT_MODEL.md
   ├─ AGENT_CARD.md
   ├─ RAPPORT_REDTEAM.md
   ├─ RAPPORT_BLUETEAM.md
   ├─ RUNBOOK.md
   └─ diagrammes.md
```

## 8. Dépendances

`langgraph`, `langchain-groq`, `astrapy`, `python-dotenv`, `reportlab`.

## 9. Exemples

**Analyse d'un doublon frauduleux :**
```bash
python agent_financier.py ask "Analyse les factures MegaConsulting FAC-2026-102 et FAC-2026-117"
```
Extrait de sortie :
```json
{
  "risk_score": 84,
  "decision": "SUSPECT_ESCALADE",
  "graph_paths": [
    "FAC-2026-117 -[DOUBLON_DE]-> FAC-2026-102",
    "FAC-2026-102 -[DEMANDEE_PAR]-> Omar Chraibi",
    "FAC-2026-102 -[VALIDEE_PAR]-> Omar Chraibi",
    "MegaConsulting -[A_RISQUE]-> Risque élevé"
  ],
  "human_validation": {
    "requis": true,
    "motifs": ["score de risque 84 > 70", "fraude détectée", "montant 120000 EUR > 100000 EUR"]
  }
}
```

**Schéma de sortie garanti** (10 champs) :
`risk_score`, `decision`, `summary`, `evidence`, `graph_paths`, `vector_sources`,
`recommendations`, `security_checks`, `human_validation`, `metadata`.
