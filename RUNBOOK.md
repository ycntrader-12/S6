# Runbook — Agent Finance Hybride V1

Guide opérationnel rapide pour démarrer, exploiter et dépanner l'agent.

## Démarrage
```bash
cd finance-fraude-agent
pip install -r requirements.txt
# 1re fois seulement : construire le graphe + l'index vectoriel
python agent_financier.py index
# Vérifier :
python agent_financier.py graph        # doit lister ~28 triplets
python agent_financier.py demo         # 4 scénarios, JSON valide
```
> Windows : `` $env:PYTHONIOENCODING='utf-8' `` si les accents s'affichent mal.

## Arrêt
Agent stateless lancé à la demande (aucun démon). Pour un service API : arrêter le
processus (Ctrl-C / `systemctl stop`). Astra reste disponible côté DataStax.

## Rollback
- **Code :** revenir au commit précédent (git).
- **Données graphe :** ré-indexer depuis la copie locale `triplets_finance.json`
  (`python agent_financier.py index` régénère les collections proprement — `delete_many`
  puis `insert_many`).
- **Workflow Langflow :** ré-importer `Indexation-GraphRAG-Finance.json`.

## Monitoring
- **Audit :** suivre `audit_log.jsonl` (1 ligne JSON / nœud : correlation_id,
  node, status, duration_ms, cost_usd, token_usage).
  ```bash
  # dernières exécutions
  tail -n 20 audit_log.jsonl
  # coût cumulé approximatif
  python -c "import json;print(sum(json.loads(l)['cost_usd'] for l in open('audit_log.jsonl',encoding='utf-8')))"
  ```
- **Sécurité :** relancer `python redteam.py` après chaque changement de policies
  (objectif : 15/15).

## Gestion des erreurs
| Symptôme | Cause probable | Action |
|---|---|---|
| `JSONDecodeError` à l'extraction | LLM a renvoyé du texte hors JSON | déjà géré (`_parser_json_llm` isole le bloc) ; sinon ré-exécuter |
| `fallback (...)` dans un expert | timeout / rate limit Groq | Blue Team : score neutre + reco « refaire » ; réessayer |
| `charmap codec can't encode` | console Windows cp1252 | `` $env:PYTHONIOENCODING='utf-8' `` |
| collections vides | indexation non lancée | `python agent_financier.py index` |
| `bloque / R7-RATE` inattendu | > 10 requêtes/min | attendre 1 min ou `sec.reset_rate_limit()` en batch |
| Astra `Unauthorized` | token expiré | regénérer le token, mettre à jour `.env` |

## Rotation des clés
1. Générer un nouveau token Astra (page de la base → *Generate Token*).
2. Générer une nouvelle clé Groq si compromise.
3. Mettre à jour `.env` (ou le secret manager) — **ne jamais** committer `.env`.
4. Relancer `demo` pour valider, puis `redteam.py`.

## Mise à jour
- **Corpus :** éditer `corpus_finance.py` → `python agent_financier.py index` → `python generer_pdfs.py`.
- **Policies :** éditer `securite.py` → `python securite.py` (auto-test) → `python redteam.py`.
- **Dépendances :** `pip install -U -r requirements.txt` puis rejouer `demo`.

## Incidents
1. **Fuite suspectée (PII/secret en sortie)** : couper le service, inspecter
   `audit_log.jsonl` par `correlation_id`, renforcer `MOTIFS_FUITE`/`masquer_pii`, rejouer Red Team.
2. **Poisoning du graphe** : ré-indexer depuis `triplets_finance.json` propre, restreindre
   l'action `indexer` au rôle `admin`, auditer les accès Astra.
3. **Faux positif de fraude** : le HITL permet au contrôleur de **corriger/rejeter** ;
   la correction est consignée dans `human_validation.correction`.

## FAQ
- **L'agent peut-il payer / bloquer une facture ?** Non. Lecture seule ; il recommande, un humain décide.
- **Que se passe-t-il si le risque > 70 ?** Escalade HITL automatique avant toute décision.
- **Le JSON peut-il être invalide ?** Non : il est construit en Python et vérifié par `valider_json`.
- **Où sont les preuves ?** Champs `evidence` (anomalie + preuve), `graph_paths`, `vector_sources`.
- **Cela touche-t-il les labs précédents dans Astra ?** Non : collections dédiées
  `triplets_finance` / `chunks_finance`.
