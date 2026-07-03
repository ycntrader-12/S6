# Documentation technique — Agent Finance Hybride V1

## 1. Objectif

Ce projet implémente un agent financier hybride capable d'analyser des dossiers de facturation et de détecter des anomalies comptables, des risques de fraude, des erreurs de TVA, des doublons de factures, des violations de politique interne, ainsi que des risques réglementaires.

Le système combine :
- un index vectoriel RAG basé sur Astra Vector avec des documents métiers,
- un Knowledge Graph stocké dans Astra sous forme de triplets,
- un pipeline multi-agent LangGraph,
- un circuit de sécurité et de Human-In-The-Loop (HITL),
- une interface graphique locale Tkinter pour l'interaction.

## 2. Architecture globale

### 2.1 Flux principal

1. `agent_financier.py index`
   - construit le graphe Astra `triplets_finance` et l'index vectoriel `chunks_finance`.
2. `agent_financier.py ask "..."`
   - lance le pipeline d'analyse pour un dossier financier.
3. `agent_financier.py graph`
   - affiche localement les triplets chargés.
4. `agent_financier.py demo`
   - teste quatre scénarios d'exécution.

### 2.2 Pipeline LangGraph

Le pipeline est défini par un `StateGraph` dans `agent_financier.py` :

- `coordinateur` : sécurité d'entrée, validation des entrées et traçabilité.
- `recherche_vecteur` : récupération du contexte documentaire via l'index Astra vectoriel.
- `recherche_graphe` : recherche multi-hop dans le Knowledge Graph local/Astra.
- `fusion` : fusionne les deux contextes en un seul bloc.
- `expert_comptable` / `expert_tva` / `expert_fraude` / `expert_conformite` : analyses spécialisées.
- `score_risque` : agrège les résultats des experts.
- `hitl` : déclenchement du circuit humain si nécessaire.
- `rapport` / `refus` : construction d'une sortie JSON sécurisée.

### 2.3 Schéma technique

```text
Client -> agent_financier.py (ask/index/demo)
               |
               v
      +-----------------------+
      | StateGraph pipeline    |
      |-----------------------|
      | coordinateur           |
      | recherche_vecteur      |--> Astra chunks_finance
      | recherche_graphe       |--> Astra triplets_finance / triplets_finance.json
      | fusion                 |
      | expert_comptable       |
      | expert_tva             |
      | expert_fraude          |
      | expert_conformite      |
      | score_risque           |
      | hitl (optionnel)       |
      | rapport / refus        |
      +-----------------------+
               |
               v
           sortie JSON
```

## 3. Composants principaux

### 3.1 `agent_financier.py`

Rôle principal du projet :
- chargement des variables d'environnement via `.env`,
- interface avec Groq LLM (`langchain_groq`),
- connexion à Astra via `astrapy`,
- définition du pipeline LangGraph,
- fonctions d'indexation, de recherche et d'assemblage du JSON final.

Fonctions clés :
- `get_llm()` : configure le modèle Groq,
- `get_db()` : crée le client Astra,
- `index_graphe()` : stocke les triplets dans Astra et en local,
- `index_vecteur()` : vectorise le corpus (`CORPUS`) et stocke les chunks Astra,
- `recherche_graphe()` / `recherche_vecteur()` : récupère le contexte métier,
- `interroger()` : point d'entrée principal pour l'analyse.

### 3.2 `securite.py`

Contient les règles de sécurité et de filtration :
- validation de l'entrée,
- détection d'injection, PII, secrets, adversarial queries,
- validation de sortie JSON,
- journalisation d'audit,
- limites de débit et gestion RBAC.

### 3.3 `corpus_finance.py`

Contient le corpus métier utilisé pour l'index vectoriel et le prompt d'extraction.
Ce fichier est la source principale des documents métiers du RAG.

### 3.4 `obsidian_ingest.py`

Module d'ingestion Obsidian :
- lit récursivement un vault Markdown,
- supprime le frontmatter YAML,
- normalise les documents pour pouvoir les indexer.

### 3.5 `chatbot_gui.py`

Interface graphique locale en Tkinter :
- lance l'indexation,
- envoie des requêtes utilisateur,
- affiche la réponse JSON,
- exécute des scénarios de démonstration.

## 4. Données et stockage

### 4.1 Collections Astra

- `triplets_finance` : stocke le Knowledge Graph.
- `chunks_finance` : stocke les documents vectorisés pour la recherche RAG.

### 4.2 Fichiers locaux

- `.env` : configuration des clés et endpoints.
- `triplets_finance.json` : copie locale du graphe extrait,
- `audit_log.jsonl` : journal d'exécution pour la traçabilité,
- `docs_pdf/` : PDF générés servant de documentation de corpus.

## 5. Configuration

Le projet utilise un fichier `.env` contenant :

```dotenv
GROQ_API_KEY=...
ASTRA_DB_API_ENDPOINT=...
ASTRA_DB_APPLICATION_TOKEN=...
```

### 5.1 Variable `GROQ_API_KEY`

Clé API pour Groq / modèle LLM `llama-3.3-70b-versatile`.

### 5.2 Variables Astra

- `ASTRA_DB_API_ENDPOINT` : URL de la base Astra,
- `ASTRA_DB_APPLICATION_TOKEN` : token applicatif Astra avec droits lecture/écriture.

## 6. Exécution

### 6.1 Préparer l'environnement

```powershell
cd "D:\agentic\29 juin au 03 juillet\Vendredi\finance-fraude-agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 6.2 Indexation

```powershell
python agent_financier.py index
```

### 6.3 Analyse

```powershell
python agent_financier.py ask "Analyse la facture FAC-2026-102"
```

### 6.4 Vérification du graphe

```powershell
python agent_financier.py graph
```

### 6.5 Interface graphique

```powershell
python chatbot_gui.py
```

## 7. Sécurité et validation

- La sortie finale est validée en JSON via `sec.valider_json`.
- Le module `securite.py` masque les données sensibles et applique la politique de sécurité.
- Le circuit HITL est déclenché quand le score de risque, le montant ou la confiance dépassent des seuils.
- Les logs d'audit sont écrits dans `audit_log.jsonl`.

## 8. Extensions possibles

### 8.1 Utiliser du contenu Obsidian

- `obsidian_ingest.py` peut charger un vault Markdown,
- ce contenu peut ensuite être ajouté au corpus ou index vectoriellement.

### 8.2 Ajouter un adaptateur Skill Specture

- ajouter un module d'intégration dédié,
- exposer `interroger()` via un runtime Skill/agent.

### 8.3 Déployer derrière une API

- créer un wrapper FastAPI autour de `interroger()`,
- gérer l'authentification, les quotas et la supervision.

## 9. Dépannage rapide

- `401 Unauthorized` Astra : vérifier `ASTRA_DB_APPLICATION_TOKEN` et `ASTRA_DB_API_ENDPOINT`.
- `Invalid API Key` Groq : vérifier `GROQ_API_KEY`.
- collections vides : ré-exécuter `python agent_financier.py index`.
- erreurs JSON : vérifier le module `securite.py` et le parser `_parser_json_llm`.

## 10. Fichiers clés

- `agent_financier.py` : cœur du système,
- `securite.py` : policies, audit et validation,
- `corpus_finance.py` : contenu métier du RAG,
- `chatbot_gui.py` : interface graphique,
- `obsidian_ingest.py` : ingestion Markdown Obsidian,
- `RUNBOOK.md` : guide opérationnel.

## 11. Glossaire technique

- **RAG** : Retrieval-Augmented Generation, combinaison d'un index vectoriel et d'un modèle de langage.
- **HITL** : Human-In-The-Loop, circuit de validation humaine pour les rapports sensibles.
- **Astra** : base de données managée DataStax utilisée ici pour stocker graphes et vecteurs.
- **triplet** : relation structurée `source-relation-cible` dans le Knowledge Graph.
- **Vector Search** : recherche sémantique basée sur des embeddings de documents.

## 12. Tests et validation

- `python agent_financier.py demo` : exécute 4 scénarios d'analyse et vérifie la sortie JSON.
- `python agent_financier.py graph` : affiche les triplets stockés pour vérifier la persistance.
- `python generer_pdfs.py` : génère les documents de corpus en PDF pour inspection.
- `python redteam.py` : lance les tests d'attaque adversariale pour vérifier les politiques de sécurité.

## 13. Limitations et améliorations

- Le module LLM dépend des clés Groq ; en cas de clé invalide, l'agent ne peut pas extraire ni analyser.
- L'indexation vectorielle dépend de l'API Astra Vector ; un token incorrect ou un endpoint erroné bloque la connexion.
- L'agent n'effectue aucune action sur les paiements : il ne recommande que des décisions, sans automatisation de paiement.
- Améliorations possibles :
  - ajout d'un module Skill Specture pour exposition comme skill/action,
  - wrapper FastAPI pour transformer `interroger()` en service web,
  - enrichissement du corpus avec des notes Obsidian et des PDF supplémentaires.
