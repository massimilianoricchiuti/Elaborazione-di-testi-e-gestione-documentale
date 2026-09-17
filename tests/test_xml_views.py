"""Regression checks for XML content previously omitted by the detail page."""

from lxml import html

from src.processing.site_builder import _environment
from src.processing.xml_view import read_xml_document
from src.support.config import PATHS
from src.support.xml_utils import parse_xml


def test_every_archived_xml_is_fully_represented(built_project):
    for path in sorted(built_project.xml_dir.glob("*.xml")):
        tree = parse_xml(path)
        cig = tree.getroot().get("cig")
        page = html.parse(str(built_project.dist / "cig" / f"{cig}.html"))
        download = built_project.dist / "downloads" / "xml" / path.name
        assert download.read_bytes() == path.read_bytes(), cig
        assert not page.xpath('//*[@id="codice-xml" or @id="xml-source-code"]')
        rendered = page.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " xml-node ")]')
        assert [node.get("data-xml-path") for node in rendered] == [tree.getpath(node) for node in tree.getroot().iter()], cig
        for element, node in zip(tree.getroot().iter(), rendered):
            # Inspect only this node's opening tag, not its descendants.
            opening = node.xpath('./summary/code | ./code')[0]
            names = opening.xpath('.//span[@class="xml-attribute-name"]/text()')
            values = opening.xpath('.//span[@class="xml-attribute-value"]/text()')
            assert dict(zip(names, [value[1:-1] for value in values])) == dict(element.attrib), (cig, element.tag)
            if len(element) == 0:
                rows = page.xpath('//*[@id="scheda"]//div[@data-xml-path=$path]', path=tree.getpath(element))
                assert len(rows) == 1, (cig, element.tag)
                expected = (element.text or "").strip()
                if expected:
                    assert rows[0].xpath('./dd/span[@class="field-value"]')[0].text_content() == expected
                else:
                    assert rows[0].xpath('./dd/span[@class="empty-value"]'), (cig, element.tag)


def test_mixed_content_repeats_and_escaping_are_preserved(tmp_path):
    path = tmp_path / "mixed.xml"
    path.write_text('<contratto cig="TEST" fonte="ANAC"><descrizioneDocumentale>Prima <oggetto>&lt;script&gt; &amp; dati</oggetto>, poi <oggetto attributo="&quot;test&quot;">secondo</oggetto>.</descrizioneDocumentale><cup/></contratto>', encoding="utf-8")
    document = read_xml_document(path)
    mixed = document["root"]["children"][0]
    assert [part["kind"] for part in mixed["content"]] == ["text", "element", "text", "element", "text"]
    assert mixed["value"] == "Prima <script> & dati, poi secondo."
    assert mixed["children"][1]["path"].endswith("oggetto[2]")
    assert document["root"]["children"][1]["empty"]
    template = _environment(PATHS).get_template("xml_tree.html")
    rendered = str(template.module.render_xml_node(document["root"]))
    assert not html.fromstring(rendered).xpath(".//script")
    assert "&lt;script&gt; &amp; dati" in rendered
    assert "Prima " in rendered and ", poi " in rendered


def test_home_integration_and_document_view_links(built_project):
    home = html.parse(str(built_project.dist / "index.html"))
    assert home.xpath('//*[@id="progetto-e-metodo"]//h2[text()="Progetto e metodo"]')
    assert home.xpath('//*[@id="documentazione"]')
    sections = home.xpath('//section[contains(concat(" ", normalize-space(@class), " "), " home-section ")]/@id')
    anchors = home.xpath('//nav[@aria-label="Sezioni della Home"]//a/@href')
    assert anchors == [f"#{section}" for section in sections]
    assert len(sections) == 6
    assert home.xpath('//a[text()="ANAC"]/@href') == ['https://www.anticorruzione.it/-/piattaforma-contratti-pubblici']
    assert not home.xpath('//header//a[contains(@href,"progetto.html")]')
    assert home.xpath('//header//span[text()="WebCig"]')
    assert "ELABORAZIONE DI TESTI E GESTIONE DOCUMENTALE" not in home.getroot().text_content()
    legacy = html.parse(str(built_project.dist / "progetto.html"))
    assert legacy.xpath('//meta[@http-equiv="refresh"]/@content') == ['0;url=index.html#progetto-e-metodo']
    for file in built_project.dist.rglob("*.html"):
        page = html.parse(str(file))
        ids = page.xpath('//*[@id]/@id')
        assert len(ids) == len(set(ids)), file
        for link in page.xpath('//a[starts-with(@href,"#")]/@href'):
            assert link[1:] in ids, (file, link)
