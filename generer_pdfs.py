# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR DES PDF DU CORPUS FINANCIER
======================================
Transforme les 6 documents du corpus (corpus_finance.CORPUS) en fichiers PDF
individuels dans le dossier docs_pdf/. Ces PDF sont la source « documentation PDF »
citée dans le cahier des charges pour le RAG vectoriel.

Usage :
    python generer_pdfs.py
"""

import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from corpus_finance import CORPUS

ICI = os.path.dirname(__file__)
DOSSIER = os.path.join(ICI, "docs_pdf")
BLEU = colors.HexColor("#1f4e79")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titre", parent=s["Title"], textColor=BLEU, fontSize=18))
    s.add(ParagraphStyle("Corps", parent=s["BodyText"], fontSize=11, leading=16,
                         alignment=4, spaceAfter=8))
    return s


def decouper_documents() -> list:
    """Découpe le corpus en (titre, corps) par bloc 'DOC n — TITRE : ...'."""
    blocs = [b.strip() for b in CORPUS.strip().split("\n\n") if b.strip()]
    docs = []
    for b in blocs:
        m = re.match(r"(DOC\s*\d+\s*—\s*[^:]+):\s*(.*)", b, re.DOTALL)
        if m:
            docs.append((m.group(1).strip(), m.group(2).strip()))
        else:
            docs.append(("Document", b))
    return docs


def generer():
    os.makedirs(DOSSIER, exist_ok=True)
    s = _styles()
    for i, (titre, corps) in enumerate(decouper_documents(), 1):
        nom = re.sub(r"[^\w]+", "_", titre.lower()).strip("_")
        chemin = os.path.join(DOSSIER, f"{i:02d}_{nom}.pdf")
        doc = SimpleDocTemplate(chemin, pagesize=A4,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        elements = [
            Paragraph("Agent Finance V1 — Documentation interne", s["Corps"]),
            Spacer(1, 0.3 * cm),
            Paragraph(titre, s["Titre"]),
            Spacer(1, 0.5 * cm),
            Paragraph(corps.replace("\n", " "), s["Corps"]),
        ]
        doc.build(elements)
        print(f">> PDF généré : {chemin}")
    print(f"\n>> {i} PDF écrits dans {DOSSIER}")


if __name__ == "__main__":
    generer()
