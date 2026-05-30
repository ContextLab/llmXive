# tests/unit/test_grounding_full_text.py
from llmxive.grounding.full_text import RetrievedDoc, html_to_text


def test_retrieved_doc_readable_flag():
    assert RetrievedDoc(kind="doi", value="10.x/y", tier=None, full_text=None,
                        abstract=None, title=None, final_url="", error="e").readable is False
    assert RetrievedDoc(kind="doi", value="10.x/y", tier="unpaywall",
                        full_text="body", abstract=None, title=None,
                        final_url="u", error=None).readable is True
    assert RetrievedDoc(kind="doi", value="10.x/y", tier="s2", full_text=None,
                        abstract="abs only", title=None, final_url="u",
                        error=None).readable is True


def test_html_to_text_strips_tags_and_scripts():
    html = ("<html><head><title>T</title><style>.x{}</style>"
            "<script>var a=1;</script></head><body><h1>Result</h1>"
            "<p>The correlation was r=0.42 across knots.</p></body></html>")
    text = html_to_text(html, max_chars=10_000)
    assert "r=0.42 across knots" in text
    assert "var a=1" not in text and ".x{}" not in text


def test_extract_pdf_text_caps_length():
    # extract_pdf_text post-processes already-extracted page strings; feed raw text
    from llmxive.grounding.full_text import _normalize_extracted
    big = "word " * 100_000
    out = _normalize_extracted(big, max_chars=1000)
    assert len(out) <= 1000
    assert "  " not in out  # whitespace collapsed
