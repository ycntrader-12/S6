# -*- coding: utf-8 -*-
"""
Outils d'ingestion pour un vault Obsidian (Markdown).

Fonctions:
- load_vault(vault_path) -> list[str]
  Recherche récursive des fichiers .md et renvoie leur contenu (sans frontmatter).

"""
from __future__ import annotations

import os
import re
from typing import List


def _strip_frontmatter(text: str) -> str:
    # enlève un frontmatter YAML délimité par '---' en début de fichier
    if text.startswith("---"):
        parts = text.split('---', 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text


def load_vault(vault_path: str) -> List[str]:
    """Lit récursivement les fichiers Markdown dans `vault_path`.
    Retourne une liste de documents (chaque fichier comme un document brut).
    """
    docs: List[str] = []
    vault_path = os.path.abspath(vault_path)
    if not os.path.isdir(vault_path):
        raise FileNotFoundError(f"Vault introuvable: {vault_path}")

    for root, _, files in os.walk(vault_path):
        for f in files:
            if f.lower().endswith('.md'):
                p = os.path.join(root, f)
                try:
                    with open(p, 'r', encoding='utf-8') as fh:
                        txt = fh.read()
                    txt = _strip_frontmatter(txt)
                    # Normaliser les sauts de ligne et enlever les balises de code longues
                    txt = re.sub(r"\r\n", "\n", txt)
                    docs.append(txt.strip())
                except Exception:
                    # ignorer les fichiers non lisibles
                    continue
    return docs
