# Diagrammes — Agent Finance Hybride V1

## 1. Flowchart — pipeline de l'agent

```mermaid
flowchart TD
    A([Dossier financier]) --> B[Agent Coordinateur<br/>garde d'entrée]
    B -->|BLOQUE| R[Refus JSON sécurisé]
    B -->|AUTORISE| V[Agent Vector Search<br/>chunks_finance]
    V --> G[Agent Graph Search<br/>triplets_finance multi-hop]
    G --> F[Fusion des résultats]
    F --> E1[Expert Comptable]
    E1 --> E2[Expert TVA]
    E2 --> E3[Expert Fraude]
    E3 --> E4[Expert Conformité]
    E4 --> S[Calcul du Score de Risque]
    S -->|risque>70 / fraude / >100k€ / conf<80%| H[Human In The Loop]
    S -->|sinon| J[Rapport Final JSON]
    H -->|approuvé / corrigé| J
    H -->|rejeté| R
    J --> OUT([Sortie JSON valide])
    R --> OUT
```

## 2. Sequence Diagram

```mermaid
sequenceDiagram
    actor U as Analyste
    participant C as Coordinateur
    participant VS as Vector Search
    participant GS as Graph Search
    participant EX as Experts (x4)
    participant SR as Score de Risque
    participant H as HITL (Contrôleur)
    participant A as Astra DB
    participant L as LLM Groq

    U->>C: dossier financier
    C->>C: garde_entree (injection/PII/secrets/DoS)
    alt bloqué
        C-->>U: Refus JSON
    else autorisé
        C->>VS: rechercher
        VS->>A: $vectorize (chunks_finance)
        A-->>VS: top-k documents
        C->>GS: rechercher
        GS->>A: triplets_finance
        A-->>GS: triplets (multi-hop)
        GS->>EX: contexte fusionné
        EX->>L: prompts experts (comptable/TVA/fraude/conformité)
        L-->>EX: anomalies + preuves
        EX->>SR: analyses
        SR->>SR: score + confiance + fraude + montant
        alt seuils HITL atteints
            SR->>H: escalade
            H-->>SR: approuve / corrige / rejette
        end
        SR-->>U: Rapport Final JSON (+ audit_log)
    end
```

## 3. Architecture Diagram

```mermaid
flowchart LR
    subgraph Client
        U[Analyste / Contrôleur]
    end
    subgraph Agent["Agent LangGraph (sandbox lecture seule)"]
        SEC[Policies sécurité<br/>securite.py]
        ORCH[Orchestrateur<br/>agent_financier.py]
        TRACE[Traçabilité<br/>audit_log.jsonl]
    end
    subgraph Astra["Astra DB (DataStax)"]
        KG[(triplets_finance<br/>Knowledge Graph)]
        VEC[(chunks_finance<br/>Vector RAG)]
    end
    LLM[[Groq llama-3.3-70b]]
    PDF[docs_pdf/*.pdf<br/>corpus source]

    U --> SEC --> ORCH
    ORCH -->|recherche_graphe| KG
    ORCH -->|recherche_vecteur| VEC
    ORCH -->|llm_groq| LLM
    PDF -. indexation .-> VEC
    PDF -. extraction triplets .-> KG
    ORCH --> TRACE
    ORCH --> U
```

## 4. Knowledge Graph — modèle de données (multi-hop)

```mermaid
flowchart TD
    ENT[Entreprise] --> FAC[Facture]
    FAC -->|EMISE_PAR| FOU[Fournisseur]
    FAC -->|IMPUTEE_SUR| CPT[Compte comptable]
    FAC -->|AFFECTEE_AU_CENTRE| CC[Centre de coût]
    FAC -->|VALIDEE_PAR| EMP[Employé]
    FAC -->|DEMANDEE_PAR| EMP
    FAC -->|DOUBLON_DE| FAC2[Autre Facture]
    FAC -->|VIOLE| POL[Politique / Règle]
    FOU -->|LIEE_AU_CONTRAT| CTR[Contrat]
    FOU -->|A_RISQUE| RISK[Motif de risque]
    CTR -->|RATTACHEE_AU_PROJET| PRJ[Projet]
    PRJ -->|GERE_PAR| DEP[Département]
    DEP -->|DIRIGE| RESP[Responsable]

    classDef alert fill:#ffe0e0,stroke:#c0392b;
    class FAC2,RISK,POL alert;
```

**Chemin multi-hop illustratif détecté par l'agent :**
`FAC-2026-102 → EMISE_PAR → MegaConsulting → A_RISQUE → offshore non agréé`
puis `FAC-2026-117 → DOUBLON_DE → FAC-2026-102` et
`FAC-2026-102 → DEMANDEE_PAR / VALIDEE_PAR → Omar Chraibi` (auto-validation).
