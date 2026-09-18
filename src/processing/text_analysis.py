from __future__ import annotations

from collections import defaultdict

import spacy
from spacy.tokens import Doc

from src.support.config import ProjectPaths
from src.support.io_utils import write_json
from src.support.xml_utils import parse_xml, xpath_text

MODEL = "it_core_news_sm"
TEXT_XPATH = "/contratto/informazioniGara/oggettoGara"
TOP_TERMS = 20
# Correzione lessicale verificata nel corpus; vale per tutti i documenti.
LEMMA_CORRECTIONS = {"arredi": "arredo"}


def _highlight_parts(text: str, matches: list[tuple[int, int]]) -> list[dict]:
    """Separa testo e occorrenze, lasciando al template l'escaping HTML."""
    parts = []
    cursor = 0
    for start, end in matches:
        if start > cursor:
            parts.append({"text": text[cursor:start], "match": False})
        parts.append({"text": text[start:end], "match": True})
        cursor = end
    if cursor < len(text):
        parts.append({"text": text[cursor:], "match": False})
    return parts


def analyze_text(paths: ProjectPaths) -> dict:
    """Conta i lemmi negli oggetti di gara e conserva ogni riscontro nel testo."""
    nlp = spacy.load(MODEL, exclude=["parser"])
    files = sorted(paths.xml_dir.glob("*.xml"))
    terms = {}
    documents_with_text = 0
    tokens = 0

    for path in files:
        tree = parse_xml(path)
        text = xpath_text(tree, TEXT_XPATH)
        if not text:
            continue
        documents_with_text += 1
        cig = tree.getroot().get("cig", "")
        authority = xpath_text(tree, "/contratto/stazioneAppaltante/denominazione")

        # Gli oggetti sono spesso tutti maiuscoli. Il modello legge in minuscolo;
        # i token originali conservano grafia e posizioni per le concordanze.
        original = nlp.make_doc(text)
        normalized = Doc(
            nlp.vocab,
            words=[token.lower_ for token in original],
            spaces=[bool(token.whitespace_) for token in original],
        )
        matches = defaultdict(list)
        for token, source in zip(nlp(normalized), original):
            if token.pos_ not in {"NOUN", "ADJ"} or not token.is_alpha or token.is_stop or token.ent_type_ or len(token) < 3:
                continue
            lemma = LEMMA_CORRECTIONS.get(token.lower_, token.lemma_.lower())
            term = terms.setdefault(lemma, {"lemma": lemma, "count": 0, "forms": set(), "concordances": []})
            term["count"] += 1
            term["forms"].add(source.text.lower())
            matches[lemma].append((source.idx, source.idx + len(source)))
            tokens += 1

        # Un solo estratto per lemma e CIG: tutte le occorrenze sono evidenziate.
        for lemma, positions in matches.items():
            terms[lemma]["concordances"].append({
                "cig": cig,
                "authority": authority,
                "field": "Oggetto della gara",
                "count": len(positions),
                "parts": _highlight_parts(text, positions),
            })

    ranked = sorted(terms.values(), key=lambda term: (-term["count"], term["lemma"]))
    top_terms = [
        {
            **term,
            "forms": sorted(term["forms"]),
            "document_count": len({item["cig"] for item in term["concordances"]}),
        }
        for term in ranked[:TOP_TERMS]
    ]
    result = {
        "documents": len(files),
        "documents_with_text": documents_with_text,
        "tokens": tokens,
        "distinct_lemmas": len(terms),
        "source_xpath": TEXT_XPATH,
        "model": {"name": MODEL, "version": nlp.meta["version"], "spacy_version": spacy.__version__},
        "method": "Nomi comuni e aggettivi di almeno tre caratteri, esclusi stopword, entità riconosciute, numeri e punteggiatura; un oggetto di gara per XML.",
        "lemma_corrections": LEMMA_CORRECTIONS,
        "top_terms": top_terms,
    }
    write_json(paths.output_data / "text_analysis.json", result)
    return result
