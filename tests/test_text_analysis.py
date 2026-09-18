import json
from dataclasses import replace

from lxml import etree, html

from src.processing.site_builder import _environment
from src.processing.text_analysis import _highlight_parts, analyze_text
from src.support.config import PATHS
from src.support.xml_utils import parse_xml, xpath_text


def test_lemmas_counts_and_original_text(tmp_path):
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    texts = [
        "MANUTENZIONE DEGLI IMPIANTI E FORNITURA DI SERVIZI.  Manutenzione dell'impianto.",
        "Fornitura di servizi per gli impianti.",
        "",
    ]
    for index, text in enumerate(texts):
        root = etree.Element("contratto", cig=f"TEST{index}")
        info = etree.SubElement(root, "informazioniGara")
        etree.SubElement(info, "oggettoGara").text = text
        # Una copia nel lotto e la frase generata non devono gonfiare le frequenze.
        etree.SubElement(info, "oggettoLotto").text = text
        etree.SubElement(root, "descrizioneDocumentale").text = "Procedura avente per oggetto un servizio."
        etree.ElementTree(root).write(str(xml_dir / f"{index}.xml"), encoding="utf-8")

    result = analyze_text(replace(PATHS, xml_dir=xml_dir, output_data=tmp_path / "data"))
    terms = {term["lemma"]: term for term in result["top_terms"]}
    assert result["documents"] == 3
    assert result["documents_with_text"] == 2
    assert terms["impianto"]["forms"] == ["impianti", "impianto"]
    assert terms["impianto"]["count"] == 3
    assert terms["impianto"]["document_count"] == 2
    assert terms["servizio"]["count"] == 2
    assert "oggetto" not in terms
    for term in terms.values():
        for item in term["concordances"]:
            original = texts[int(item["cig"].removeprefix("TEST"))]
            assert "".join(part["text"] for part in item["parts"]) == original
            assert sum(part["match"] for part in item["parts"]) == item["count"]


def test_concordance_text_is_escaped():
    original = 'Servizi <script>alert("x")</script> & manutenzione'
    result = {
        "documents_with_text": 1,
        "top_terms": [{
            "lemma": "servizio", "forms": ["servizi"], "count": 1, "document_count": 1,
            "concordances": [{
                "cig": "TEST", "authority": "Ente", "field": "Oggetto della gara", "count": 1,
                "parts": _highlight_parts(original, [(0, 7)]),
            }],
        }],
    }
    rendered = _environment(PATHS).get_template("lexicon.html").render(text_analysis=result)
    page = html.fromstring(rendered)
    assert not page.xpath(".//script")
    assert page.xpath(".//blockquote")[0].text_content() == original
    assert page.xpath(".//mark/text()") == ["Servizi"]


def test_corpus_concordances_are_traceable(built_project):
    result = json.loads((built_project.output_data / "text_analysis.json").read_text())
    page = html.parse(str(built_project.dist / "report.html"))
    entries = page.xpath('//*[@id="lessico"]//details[@class="lexicon-entry"]')
    assert len(entries) == len(result["top_terms"]) == 20
    terms = {term["lemma"]: term for term in result["top_terms"]}
    assert terms["arredo"]["forms"] == ["arredi"]
    assert "frascato" not in terms
    for term, entry in zip(result["top_terms"], entries):
        assert term["count"] == sum(item["count"] for item in term["concordances"])
        assert term["document_count"] == len({item["cig"] for item in term["concordances"]})
        assert len(entry.xpath('.//mark')) == term["count"]
        quotes = entry.xpath('.//blockquote')
        for item, quote in zip(term["concordances"], quotes):
            tree = parse_xml(built_project.xml_dir / f"CIG_{item['cig']}.xml")
            assert quote.text_content() == xpath_text(tree, result["source_xpath"])
            assert entry.xpath('.//a[@href=$url]', url=f"cig/{item['cig']}.html#scheda")
