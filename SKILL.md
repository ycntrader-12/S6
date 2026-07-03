# SKILL.md — Agent Finance Hybride V1

## 🎯 Nom du Skill
**Agent Finance Hybride — Détection de fraude & anomalies financières**

## 📋 Description
Agent IA hybride (RAG vectoriel + Knowledge Graph) qui analyse un dossier financier d'entreprise et détecte automatiquement : incohérences comptables, risques de fraude, anomalies de TVA, doublons de factures, dépenses hors politique interne, fournisseurs à risque, transactions inhabituelles et violations réglementaires.

Produit **toujours** une sortie **JSON valide à 100 %** contenant l'analyse, un score de risque, les preuves, les sources (graphe + documents) et les recommandations, sous le contrôle d'un circuit **Human-In-The-Loop** et de **policies de sécurité** complètes.

## 🏗️ Architecture

### Type d'agent
- **Multi-agents** orchestrés via **LangGraph**
- **Hybride** : RAG vectoriel + Knowledge Graph (GraphRAG)

### Pipeline (11 étapes)

| # | Agent | Rôle |
|---|-------|------|
| 1 | **Coordinateur** | Sécurité d'entrée + ouverture de la trace d'audit |
| 2 | **Vector Search** | Recherche RAG vectoriel (politiques, procédures, normes — Astra vectorize) |
| 3 | **Graph Search** | Traversée **multi-hop** du Knowledge Graph (Facture→Fournisseur→Contrat→Projet→Département→Responsable) |
| 4 | **Fusion** | Fusionne les deux contextes (vecteur + graphe) |
| 5 | **Expert Comptable** | Détection de doublons, vérification imputation, séparation des tâches |
| 6 | **Expert TVA** | Taux incorrects, TVA non déductible, factures non conformes |
| 7 | **Expert Fraude** | Fractionnement (smurfing), offshore, auto-validation, doublons |
| 8 | **Expert Conformité** | Plafonds, seuils, loi 43-05 / 09-08 |
| 9 | **Score de Risque** | Agrégation pondérée des 4 experts |
| 10 | **Human-In-The-Loop** | Validation humaine si risque > 70, fraude, montant > 100 000 €, confiance < 80 % |
| 11 | **Rapport Final JSON** | Assemblage + garde de sortie + validation du schéma |

### Flux d'exécution
Dossier ─▶ Coordinateur ─(bloqué)─────────────────────────▶ Refus JSON
│
└(autorisé)▶ Vector Search ▶ Graph Search ▶ Fusion
│
Expert Comptable ◀─────────────────────────────────────────┘
└▶ Expert TVA ▶ Expert Fraude ▶ Expert Conformité ▶ Score de Risque
│
┌─(HITL requis)─▶ HITL ─(rejeté)─▶ Refus JSON
│ └(approuvé/corrigé)─┐
└─(sinon)──────────────────────────────┴▶ Rapport Final JSON

## 🧠 Sources de connaissance

| Source | Collection Astra | Contenu |
|--------|-----------------|---------|
| **Vector RAG** | `chunks_finance` | Politiques internes, procédures, normes comptables, documentation PDF, contrats (embeddings NVIDIA `NV-Embed-QA`) |
| **Knowledge Graph** | `triplets_finance` | Relations : Entreprise / Facture / Fournisseur / Employé / Compte / Transaction / Centre de coût / Projet (parcours multi-hop) |

## 🔧 Entrées / Sorties

### Entrée
- Un « dossier » : question ou description d'une ou plusieurs factures
- Exemple : `"Analyse la facture FAC-2026-102 de MegaConsulting"`

### Sortie (JSON garanti — 10 champs)
| Champ | Description |
|-------|-------------|
| `risk_score` | Score de risque agrégé (0-100) |
| `decision` | Décision finale (VALIDE, SUSPECT, SUSPECT_ESCALADE, REJETE) |
| `summary` | Résumé de l'analyse |
| `evidence` | Preuves détectées |
| `graph_paths` | Chemins du Knowledge Graph utilisés |
| `vector_sources` | Sources vectorielles RAG mobilisées |
| `recommendations` | Recommandations d'actions |
| `security_checks` | Résultats des vérifications de sécurité |
| `human_validation` | Besoin et statut de validation humaine |
| `metadata` | Métadonnées d'exécution |

## 🛡️ Sécurité & Policies

| Politique | Implémentation |
|-----------|---------------|
| **Anti-injection prompt** | Détection et blocage des tentatives d'injection |
| **PII / Secrets** | Masquage des données personnelles et secrets |
| **RBAC** | Contrôle d'accès basé sur les rôles |
| **Rate-limit** | Limitation du nombre de requêtes |
| **Audit trail** | Journalisation complète dans `audit_log.jsonl` |
| **Red Team** | 15 attaques OWASP LLM testées automatiquement |

## ⚙️ Configuration

| Variable d'environnement | Description |
|--------------------------|-------------|
| `GROQ_API_KEY` | Clé API Groq (LLM `llama-3.3-70b-versatile`) |
| `ASTRA_DB_API_ENDPOINT` | Endpoint de la base DataStax Astra |
| `ASTRA_DB_APPLICATION_TOKEN` | Token applicatif Astra |

## 📦 Dépendances
- `langgraph` — Orchestration multi-agents
- `langchain-groq` — Intégration LLM Groq
- `astrapy` — Client DataStax Astra DB
- `python-dotenv` — Gestion des variables d'environnement
- `reportlab` — Génération de PDF

## 🚀 Commandes

```bash
# Indexer le corpus (extrait triplets + vectorise)
python agent_financier.py index

# Analyser un dossier → JSON
python agent_financier.py ask "Analyse la facture FAC-2026-102 de MegaConsulting"

# Afficher le Knowledge Graph
python agent_financier.py graph

# Démo : 4 scénarios (fraude, injection, PII, facture conforme)
python agent_financier.py demo

# Campagne Red Team
python redteam.py

###{
  "risk_score": 84,
  "decision": "SUSPECT_ESCALADE",
  "summary": "Fraude détectée : auto-validation par Omar Chraibi, facture doublon FAC-2026-117, fournisseur à risque élevé.",
  "evidence": [
    "Doublon détecté entre FAC-2026-102 et FAC-2026-117",
    "Auto-validation : demandeur = validateur (Omar Chraibi)",
    "Montant élevé : 120 000 EUR dépasse le seuil de 100 000 EUR",
    "Fournisseur MegaConsulting classé à risque élevé"
  ],
  "graph_paths": [
    "FAC-2026-117 -[DOUBLON_DE]-> FAC-2026-102",
    "FAC-2026-102 -[DEMANDEE_PAR]-> Omar Chraibi",
    "FAC-2026-102 -[VALIDEE_PAR]-> Omar Chraibi",
    "MegaConsulting -[A_RISQUE]-> Risque élevé"
  ],
  "vector_sources": [
    "Politique interne : Séparation des tâches obligatoire",
    "Procédure : Validation hiérarchique requise > 50 000 EUR",
    "Norme comptable : Interdiction auto-validation"
  ],
  "recommendations": [
    "Escalader au directeur financier pour validation manuelle",
    "Vérifier l'authenticité de la facture FAC-2026-102",
    "Auditer les relations avec MegaConsulting",
    "Révoquer temporairement les droits de validation d'Omar Chraibi"
  ],
  "security_checks": {
    "injection_detected": false,
    "pii_masked": true,
    "rbac_authorized": true,
    "rate_limit_ok": true
  },
  "human_validation": {
    "requis": true,
    "motifs": [
      "score de risque 84 > 70",
      "fraude détectée",
      "montant 120000 EUR > 100000 EUR"
    ],
    "statut": "EN_ATTENTE"
  },
  "metadata": {
    "timestamp": "2026-07-03T14:32:15Z",
    "model": "llama-3.3-70b-versatile",
    "execution_time_ms": 3420,
    "agents_invoked": ["Coordinateur", "VectorSearch", "GraphSearch", "Fusion", "ExpertComptable", "ExpertTVA", "ExpertFraude", "ExpertConformite", "ScoreRisque", "HITL", "RapportFinal"]
  }
}

