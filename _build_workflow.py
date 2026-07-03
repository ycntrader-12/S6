# -*- coding: utf-8 -*-
"""
Construit Indexation-GraphRAG-Finance.json à partir du workflow de référence,
en ne remplaçant QUE la logique métier (corpus, prompt, nom de table).
La structure (nœuds, types, connexions, schéma) reste identique.
"""
import json
import os

REF = r"C:\Users\LENOVO\Downloads\graphrag-lab\Indexation-GraphRAG.json"
OUT = os.path.join(os.path.dirname(__file__), "Indexation-GraphRAG-Finance.json")

from corpus_finance import CORPUS, PROMPT_EXTRACTION

with open(REF, encoding="utf-8") as f:
    wf = json.load(f)

# --- métadonnées du flow ---------------------------------------------------
wf["name"] = "Indexation GraphRAG Finance"
wf["description"] = ("Pipeline GraphRAG Finance : corpus financier -> extraction de "
                     "triplets (Facture/Fournisseur/Contrat/Projet...) via LLM -> "
                     "stockage dans Astra (Cassandra Graph, table triplets_finance)")

# --- adaptation métier des nœuds (mêmes types, mêmes ids de composant) ------
for node in wf["data"]["nodes"]:
    tpl = node["data"].get("node", {}).get("template", {})
    dtype = node["data"].get("type")

    if dtype == "TextInput":                      # le corpus injecté
        tpl["input_value"]["value"] = CORPUS.strip()

    elif dtype == "Prompt Template":              # le prompt d'extraction
        # le composant de référence utilise {corpus} comme variable -> on garde
        tpl["template"]["value"] = PROMPT_EXTRACTION

    elif dtype == "CassandraGraph":               # nouvelle table Astra
        tpl["table_name"]["value"] = "triplets_finance"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

# validation : le JSON doit être rechargeable et garder la même topologie
with open(OUT, encoding="utf-8") as f:
    check = json.load(f)
assert len(check["data"]["nodes"]) == 7
assert len(check["data"]["edges"]) == 6
print(f">> Workflow écrit : {OUT}")
print(f"   nodes={len(check['data']['nodes'])} edges={len(check['data']['edges'])}")
print(f"   table Astra = triplets_finance")
