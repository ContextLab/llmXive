import os

import pytest

from llmxive.grounding.full_text import retrieve

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call"
)


def test_retrieve_arxiv_full_text():
    doc = retrieve("arxiv", "1706.03762", timeout=60.0)
    assert doc.readable and doc.full_text and len(doc.full_text) > 2000
    assert "attention" in doc.full_text.lower()
    assert doc.tier == "arxiv"


def test_retrieve_oa_doi_via_unpaywall_or_s2():
    # PLOS ONE gold-OA article (verified live 2026-05-29)
    doc = retrieve("doi", "10.1371/journal.pone.0000308", timeout=60.0)
    assert doc.readable and doc.full_text and len(doc.full_text) > 2000
    assert doc.tier in ("unpaywall", "s2", "preprint", "url")


def test_retrieve_fake_doi_unreadable():
    doc = retrieve("doi", "10.5281/zenodo.999999999999", timeout=30.0)
    assert doc.readable is False
