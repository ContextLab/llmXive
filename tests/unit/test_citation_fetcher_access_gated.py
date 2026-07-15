"""A bot-blocked/paywalled real host classifies as PENDING, not a false MISMATCH.

Real academic sources (publisher pages, OEIS behind Cloudflare, KnotInfo,
rate-limited registrars) frequently 403/401/429 an automated client — the host
EXISTS, it just gates the body. Classifying that as UNREACHABLE false-flagged
real references as fabricated. These tests pin the access-gated -> PENDING
classification while keeping 404/DNS -> MISMATCH/UNREACHABLE (the
anti-fabrication classification is preserved).

Issue #1139 D14/D15 changed what PENDING MEANS at the gate: existence is no
longer verification. A bare URL/DOI with no cross-checkable cited title now
classifies PENDING (not a false VERIFIED), and the reference gate is POSITIVE —
a project advances only when EVERY citation is VERIFIED, so PENDING now BLOCKS
(bounded retry / substitution upstream) rather than silently passing. These
tests assert the classification layer here; the positive-gate behavior lives in
``test_reference_gate_positive.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents.tools import citation_fetcher as cf

from llmxive.types import VerificationStatus


class _Resp:
    def __init__(self, status_code: int, url: str = "https://host/x", text: str = ""):
        self.status_code = status_code
        self.url = url
        self.text = text


class _Client:
    def __init__(self, resp): self._resp = resp
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def get(self, *a, **k): return self._resp


def _patch(monkeypatch, resp):
    monkeypatch.setattr(cf.httpx, "Client", lambda *a, **k: _Client(resp))


def test_url_403_is_pending_not_unreachable(monkeypatch):
    _patch(monkeypatch, _Resp(403))
    out = cf._fetch_url("https://www.worldscientific.com/doi/abs/10.1142/X",
                        cited_title="Some Knot Paper", timeout=5.0)
    assert out.status == VerificationStatus.PENDING


def test_url_429_is_pending(monkeypatch):
    _patch(monkeypatch, _Resp(429))
    out = cf._fetch_url("https://oeis.org/A002863", cited_title="OEIS seq", timeout=5.0)
    assert out.status == VerificationStatus.PENDING


def test_url_404_is_still_mismatch(monkeypatch):
    _patch(monkeypatch, _Resp(404))
    out = cf._fetch_url("https://host/missing", cited_title="x", timeout=5.0)
    assert out.status == VerificationStatus.MISMATCH


def test_url_500_is_still_unreachable(monkeypatch):
    _patch(monkeypatch, _Resp(500))
    out = cf._fetch_url("https://host/down", cited_title="x", timeout=5.0)
    assert out.status == VerificationStatus.UNREACHABLE


def test_pending_blocks_the_gate(tmp_path):
    """D15 (issue #1139): the reference gate is now POSITIVE — a project advances
    ONLY when EVERY citation is currently VERIFIED. A PENDING (present-but-
    unverified) citation now BLOCKS; a fully-VERIFIED set advances. UNREACHABLE /
    MISMATCH remain blocking (anti-fabrication gate intact). REAL round-trip
    through the production citations store + gate."""
    from datetime import UTC, datetime

    from llmxive.agents.reference_validator import has_blocking_citations
    from llmxive.state import citations as citations_store
    from llmxive.types import Citation, CitationKind

    project_id = "PROJ-901-gate"

    def _cite(status, *, cite_id="c-001"):
        return Citation(
            cite_id=cite_id,
            artifact_path=f"projects/{project_id}/specs/plan.md",
            artifact_hash="0" * 64,
            kind=CitationKind.URL,
            value="https://example.com/paper",
            cited_title="A Real Cited Title",
            verification_status=status,
            verified_at=datetime.now(UTC),
        )

    citations_store.save(project_id, [_cite(VerificationStatus.PENDING)], repo_root=tmp_path)
    assert has_blocking_citations(project_id, repo_root=tmp_path) is True

    citations_store.save(project_id, [_cite(VerificationStatus.UNREACHABLE)], repo_root=tmp_path)
    assert has_blocking_citations(project_id, repo_root=tmp_path) is True

    citations_store.save(
        project_id,
        [_cite(VerificationStatus.VERIFIED, cite_id="c-001"),
         _cite(VerificationStatus.VERIFIED, cite_id="c-002")],
        repo_root=tmp_path,
    )
    assert has_blocking_citations(project_id, repo_root=tmp_path) is False


def test_is_real_title_rejects_urls_dois_ids():
    assert cf._is_real_title("DynaCode: A Dynamic Complexity-Aware Code Benchmark") is True
    assert cf._is_real_title("https://doi.org/10.48550/arXiv.2503.10452") is False
    assert cf._is_real_title("10.48550/arXiv.2503.10452") is False
    assert cf._is_real_title("2503.10452") is False
    assert cf._is_real_title("") is False


def test_bare_url_cited_title_is_pending_not_verified():
    """D14 (issue #1139): the citation stored a URL/DOI in cited_title, so there is
    no real cited title to cross-check. The reference RESOLVED to a readable page,
    but existence != verification — classify PENDING (present-but-unverified,
    bounded retry/substitution), NOT VERIFIED on existence alone."""
    out = cf._classify_match(
        "https://doi.org/10.48550/arXiv.2503.10452",        # cited_title is a URL
        "[2503.10452] DynaCode: A Dynamic Complexity-Aware Code Benchmark",  # real title
    )
    assert out == VerificationStatus.PENDING


def test_real_title_still_mismatches_when_unrelated():
    """A genuine cited title that doesn't match a genuine (non-block) fetched title
    still MISMATCHES (anti-fabrication intact)."""
    out = cf._classify_match(
        "Attention Is All You Need", "A Totally Unrelated Paper About Sourdough Bread"
    )
    assert out == VerificationStatus.MISMATCH


def test_block_or_redirect_page_title_is_pending_not_mismatch():
    """A real reference that resolved (200) but served a JS-redirect / bot-wall /
    cookie interstitial (so the paper title can't be read) DEFERS to PENDING, not a
    fabricated-reference MISMATCH."""
    assert cf._classify_match("Seifert circles and crossing number", "Redirecting") == VerificationStatus.PENDING
    assert cf._classify_match("Some Real Paper Title Here", "Just a moment...") == VerificationStatus.PENDING
    # empty/too-short fetched title (non-HTML page, or unreadable) -> pending
    assert cf._classify_match("Some Real Paper Title Here", "") == VerificationStatus.PENDING


def test_clean_url_strips_trailing_junk():
    assert cf._clean_url("https://katlas.org`") == "https://katlas.org"
    assert cf._clean_url("https://doi.org/10.1/x).") == "https://doi.org/10.1/x"
    assert cf._clean_url("  https://ex.com/p  ") == "https://ex.com/p"


def _publisher_html(article_title: str) -> str:
    """A publisher article page whose <title> is the GENERIC journal/issue but whose
    BODY carries the real article title (the msp.org / ScienceDirect pattern)."""
    return (
        "<html><head><title>Algebraic &amp; Geometric Topology Volume 6, "
        "issue 5 (2006)</title></head><body><h1>" + article_title + "</h1>"
        "<p>Keiko Kawamuro</p></body></html>"
    )


def test_publisher_generic_title_but_article_title_in_body_is_verified(monkeypatch):
    """A real article whose page serves a GENERIC journal <title> but carries the
    cited article title in the BODY must VERIFY, not false-MISMATCH on <title> only."""
    title = "The algebraic crossing number and the braid index of knots and links"
    _patch(monkeypatch, _Resp(200, url="https://msp.org/agt/2006/6-5/p11.xhtml",
                              text=_publisher_html(title)))
    out = cf._fetch_url("https://msp.org/agt/2006/6-5/p11.xhtml",
                        cited_title="The algebraic crossing number and the braid index",
                        timeout=5.0)
    assert out.status == VerificationStatus.VERIFIED


def test_fabricated_title_absent_from_body_still_mismatches(monkeypatch):
    """SAME resolved publisher page, but a FABRICATED cited title that does NOT
    appear in the body stays MISMATCH — the body check strengthens, never weakens,
    the anti-fabrication gate."""
    _patch(monkeypatch, _Resp(200, url="https://msp.org/agt/2006/6-5/p11.xhtml",
                              text=_publisher_html("The algebraic crossing number and the braid index")))
    out = cf._fetch_url("https://msp.org/agt/2006/6-5/p11.xhtml",
                        cited_title="Invented Title About Quantum Teleportation Neural Networks",
                        timeout=5.0)
    assert out.status == VerificationStatus.MISMATCH


def test_title_in_body_requires_a_specific_phrase():
    """A too-short cited title (<4 tokens) is not body-matched (avoids coincidence);
    a full title present verbatim matches."""
    body = "<p>the algebraic crossing number and the braid index of knots</p>"
    assert cf._title_in_body("the algebraic crossing number and the braid index", body) is True
    assert cf._title_in_body("crossing number", body) is False  # 2 tokens: too short
    assert cf._title_in_body("totally different made up title", body) is False


def test_arxiv_doi_routes_to_arxiv_not_crossref(monkeypatch):
    """An arXiv DOI (DataCite, not in CrossRef) must route to the arXiv API instead
    of 404-ing on CrossRef."""
    called = {}
    def _fake_arxiv(value, *, cited_title, timeout):
        called["arxiv_id"] = value
        return cf.FetchResult(status=VerificationStatus.VERIFIED, fetched_url="x")
    monkeypatch.setattr(cf, "_fetch_arxiv", _fake_arxiv)
    out = cf._fetch_doi("10.48550/arXiv.2503.10452", cited_title="t", timeout=5.0)
    assert called.get("arxiv_id") == "2503.10452"
    assert out.status == VerificationStatus.VERIFIED
