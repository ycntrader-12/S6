# Threat Model — Agent Finance Hybride V1

## 1. Assets (biens à protéger)
| Asset | Sensibilité |
|---|---|
| Corpus financier (politiques, journal des factures, contrats) | Confidentiel |
| Knowledge Graph `triplets_finance` + index `chunks_finance` (Astra) | Confidentiel / Intégrité |
| Secrets : `GROQ_API_KEY`, token Astra (`.env`) | Critique |
| Prompt système / consignes des agents | Interne |
| Rapports d'analyse (score, preuves, décisions) | Confidentiel |
| Données personnelles employés (salaires, RIB) — **exclues** du périmètre | Critique (loi 09-08) |
| Journal d'audit `audit_log.jsonl` | Intégrité (preuve) |

## 2. Actors
- **Légitimes :** analyste financier, contrôleur (HITL), administrateur.
- **Menaçants :** utilisateur malveillant interne, attaquant externe via l'entrée,
  fournisseur cherchant à masquer une fraude, document piégé injecté dans le corpus.

## 3. Trust Boundaries
```
[Utilisateur] ──frontière 1──▶ [Garde d'entrée] ──▶ [Agents LLM + outils]
                                                        │ frontière 2
                                                        ▼
                                              [Astra DB]  [API Groq]
[Sortie JSON] ◀──frontière 3── [Garde de sortie + validation JSON]
```
- **Frontière 1 :** tout input externe est non fiable → validé avant traitement.
- **Frontière 2 :** appels sortants restreints à l'allow-list (Astra lecture, Groq).
- **Frontière 3 :** toute sortie est filtrée (PII, secrets, schéma) avant retour.

## 4. Attack Surface
Entrée texte de l'utilisateur · contenu du corpus (documents potentiellement piégés) ·
réponses du LLM · collections Astra (poisoning) · fichier `.env`.

## 5. STRIDE
| Catégorie | Menace | Contre-mesure |
|---|---|---|
| **S**poofing | Usurpation de rôle/validateur | RBAC (`ROLES`), HITL tracé par validateur |
| **T**ampering | Altération du graphe (poisoning) | Allow-list (pas d'écriture via l'agent), indexation admin only |
| **R**epudiation | Nier une action | `audit_log.jsonl` : correlation/execution id, timestamp, i/o |
| **I**nformation Disclosure | Fuite prompt / secrets / PII | Détection secrets, PII masking, anti-fuite en sortie |
| **D**enial of Service | Prompt stuffing, flood | `R6-DOS` (taille max), `R7-RATE` (rate limiting) |
| **E**levation of Privilege | Tool abuse, commandes | Sandbox lecture seule, allow-list stricte |

## 6. MITRE ATLAS (tactiques adverses IA)
| Technique ATLAS | Couverture |
|---|---|
| AML.T0051 — LLM Prompt Injection | Règles `R1`/`R2`, garde de sortie anti-fuite |
| AML.T0054 — LLM Jailbreak | `R1-INJECTION` (DAN, mode dev, « sans restriction ») |
| AML.T0057 — LLM Data Leakage | `R3-PII`, `R4-SECRETS`, PII masking |
| AML.T0043 — Craft Adversarial Data (poisoning) | Indexation réservée `admin`, agent en lecture seule |
| AML.T0034 — Cost Harvesting / DoS | `R6-DOS`, `R7-RATE`, `temperature=0` |

## 7. OWASP LLM Top 10 (2025)
| Réf | Risque | Traitement |
|---|---|---|
| LLM01 | Prompt Injection | `R1`,`R2` + anti-fuite sortie |
| LLM02 | Sensitive Info Disclosure | `R3-PII`, `R4-SECRETS`, PII masking |
| LLM03 | Supply Chain / Poisoning | Graphe alimenté par admin, agent read-only |
| LLM04 | Data & Model DoS | `R6-DOS`, `R7-RATE` |
| LLM05 | Improper Output Handling | JSON construit en Python + `valider_json` |
| LLM06 | Excessive Agency | Allow-list, sandbox, aucune action financière |
| LLM07 | System Prompt Leakage | `R2-FUITE-CONSIGNES` + `MOTIFS_FUITE` sortie |
| LLM08 | Vector/Embedding Weaknesses | Provenance des chunks tracée, sources citées |
| LLM09 | Misinformation / Hallucination | « cite ta preuve », confiance dégradée, HITL |
| LLM10 | Unbounded Consumption | Rate limiting + budget tokens tracé |

## 8. Matrice des risques (probabilité × impact)
| Risque | Prob. | Impact | Niveau | Statut |
|---|:---:|:---:|:---:|---|
| Prompt injection | Élevée | Élevé | 🔴 Critique | Mitigé (`R1/R2`) |
| Exfiltration PII/secrets | Moyenne | Élevé | 🔴 Critique | Mitigé (`R3/R4`, masking) |
| Hallucination (fausse anomalie) | Moyenne | Moyen | 🟠 Élevé | Mitigé (preuve + HITL) |
| Tool abuse / paiement | Faible | Élevé | 🟠 Élevé | Mitigé (allow-list, sandbox) |
| Graph/embedding poisoning | Faible | Élevé | 🟠 Élevé | Mitigé (read-only, admin only) |
| DoS | Moyenne | Faible | 🟡 Modéré | Mitigé (`R6/R7`) |

Résultat campagne Red Team : **15/15 attaques neutralisées** (voir `RAPPORT_REDTEAM.md`).
