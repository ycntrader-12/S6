# Agent Card — Sécurité

| Champ | Valeur |
|---|---|
| **Nom** | Agent Finance Hybride V1 — Détection de fraude & anomalies |
| **Version** | 1.0 |
| **Modèle** | Groq `llama-3.3-70b-versatile`, `temperature=0` |
| **Type** | Agent hybride RAG vectoriel + Knowledge Graph (multi-hop), orchestré par LangGraph |

## Objectif
Analyser un dossier financier d'entreprise et détecter incohérences comptables,
fraude, anomalies de TVA, doublons de factures, dépenses hors politique,
fournisseurs à risque, transactions inhabituelles et violations réglementaires ;
produire une analyse tracée, un score de risque, des preuves et des recommandations
sous contrôle humain (HITL).

## Entrées
- **Type :** texte (question ou description d'une ou plusieurs factures / dossier).
- **Contrainte :** ≤ 4000 caractères (au-delà : blocage anti-DoS `R6-DOS`).
- **Validation :** garde d'entrée déterministe (regex) avant tout traitement.

## Sorties
- **Format :** JSON strict à 10 champs (`risk_score`, `decision`, `summary`,
  `evidence`, `graph_paths`, `vector_sources`, `recommendations`,
  `security_checks`, `human_validation`, `metadata`).
- **Décisions possibles :** `CONFORME` · `A_SURVEILLER` · `SUSPECT_ESCALADE` ·
  `REJETE_PAR_VALIDATEUR` · `BLOQUE_SECURITE`.
- **Garantie :** JSON construit en Python (jamais par le LLM) → valide à 100 %.

## Outils (allow-list stricte)
`recherche_vecteur` · `recherche_graphe` · `llm_groq`.
Tout autre outil est refusé (`securite.verifier_outil`). **Lecture seule** :
aucune écriture métier, aucun paiement, aucune commande système.

## Permissions (RBAC)
| Rôle | Actions |
|---|---|
| `analyste` | analyser, consulter_graphe |
| `controleur` | + valider_hitl |
| `admin` | + indexer |

## Limites
- N'exécute aucune action financière (ne paie pas, ne bloque pas, ne sanctionne pas) :
  il **recommande**, un humain décide.
- Ne pose pas de conclusion juridique définitive (disclaimer systématique).
- Périmètre limité au corpus indexé ; hors corpus → signale l'absence d'information.
- Ne traite aucune donnée personnelle nominative (salaires, RIB) — loi 09-08.

## Hypothèses
- Le corpus (politiques, journal des factures, registre fournisseurs) est fiable
  et à jour au moment de l'indexation.
- Le LLM peut halluciner : chaque anomalie doit citer une preuve (facture / DOC / triplet),
  sinon la confiance est dégradée.

## Risques (voir THREAT_MODEL.md)
Prompt/indirect injection, jailbreak, hallucination, exfiltration de PII/secrets,
tool abuse, DoS, documents malveillants, graph/embedding poisoning.

## Guardrails
- **Entrée :** input validation, détection injection, PII, secrets, tool abuse, DoS, rate-limit.
- **Traitement :** allow-list d'outils, sandbox lecture seule, prompts experts « cite ta preuve ».
- **Sortie :** PII masking (IBAN/email), anti-fuite de consignes/secrets, validation du schéma JSON.
- **Humain :** HITL obligatoire si risque > 70 / fraude / montant > 100 000 € / confiance < 80 %.

## Politique de sécurité
Défense en profondeur (Blue Team) : validation → sanitization → policy engine →
moderation → monitoring/alertes → retry/fallback → confidence score → guardrails.
Toutes les exécutions sont journalisées (`audit_log.jsonl`).

## Métriques
- **Red Team :** 15/15 attaques neutralisées (100 %).
- **Traçabilité :** correlation_id, execution_id, timestamp, node, agent, input,
  output, status, duration, cost, model, token_usage — par nœud.

## Confiance
Score de confiance IA agrégé (0–100) par les 4 experts ; < 80 % → escalade HITL
automatique.
