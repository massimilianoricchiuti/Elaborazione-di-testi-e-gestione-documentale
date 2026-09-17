"""Build complete, presentation-only views directly from each archived XML."""

from __future__ import annotations

import re
from pathlib import Path

from src.support.xml_utils import parse_xml


_LABELS = {
    "fonti": "Fonti locali", "approfondimentiWeb": "Fonti web — metadati XML",
    "informazioniGara": "Informazioni di gara", "stazioneAppaltante": "Stazione appaltante",
    "incaricati": "Incaricati", "pubblicazioni": "Pubblicazioni",
    "partecipanti": "Partecipanti", "aggiudicazione": "Aggiudicazione",
    "contrattoEsecuzione": "Esecuzione del contratto", "quadroEconomico": "Quadro economico",
    "categorieOpera": "Categorie d’opera", "cpv": "Classificazione CPV",
    "descrizioneDocumentale": "Descrizione documentale", "tipoCig": "Tipo CIG",
    "cup": "CUP", "voceCpv": "Voce CPV", "idCategoria": "Codice categoria",
    "fonteWeb": "Fonte web", "datoFonte": "Sintesi della fonte",
    "nessoFonte": "Riscontro", "verificataIl": "Data di verifica",
}


def _label(tag: str) -> str:
    return _LABELS.get(tag, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", tag).capitalize())


def read_xml_document(path: Path) -> dict:
    """Keep all elements, attributes and ordered mixed text, apart from layout whitespace.

    No normalized analytical field is used here: new XML fields therefore appear
    without extending ContractRecord. The original XML remains downloadable.
    """
    tree = parse_xml(path)
    root = tree.getroot()
    counter = 0

    def node_view(element) -> dict:
        nonlocal counter
        counter += 1
        node_id = f"xml-node-{counter}"
        children = []
        content = []
        if element.text and element.text.strip():
            content.append({"kind": "text", "text": element.text})
        for child in element:
            if isinstance(child.tag, str):
                child_view = node_view(child)
                children.append(child_view)
                content.append({"kind": "element", "node": child_view})
            elif child.text:
                content.append({"kind": "comment", "text": child.text})
            if child.tail and child.tail.strip():
                content.append({"kind": "text", "text": child.tail})
        own_text = " ".join(part["text"] for part in content if part["kind"] == "text")
        return {
            "id": node_id, "tag": element.tag, "label": _label(element.tag),
            "path": tree.getpath(element), "attributes": dict(element.attrib),
            "children": children, "content": content,
            "value": "".join(element.itertext()).strip() if own_text.strip() else "",
            "empty": not children and not own_text.strip(),
            "search": " ".join([element.tag, own_text, *[f"{key} {value}" for key, value in element.attrib.items()]]),
        }

    root_view = node_view(root)

    def field_rows(node, context=""):
        # Parent rows retain attributes and prose around mixed-content children.
        if not node["children"] or node["attributes"] or node["value"]:
            yield {**node, "context": context}
        for child in node["children"]:
            parent = node["path"].rsplit("/", 1)[-1]
            yield from field_rows(child, f"{context} / {parent}".strip(" /"))

    sections = [
        {"id": f"dati-{node['id']}", "label": node["label"], "tag": node["tag"],
         "rows": list(field_rows(node))}
        for node in root_view["children"]
    ]
    # Put the contract first while preserving the exact XML order in the tree.
    sections.sort(key=lambda section: section["tag"] in {"fonti", "approfondimentiWeb"})
    return {
        "root": root_view, "sections": sections, "element_count": counter,
        "attribute_count": sum(len(node.attrib) for node in root.iter() if isinstance(node.tag, str)),
    }
