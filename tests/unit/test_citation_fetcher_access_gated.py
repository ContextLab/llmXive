"""A bot-blocked/paywalled real host must NOT hard-block advancement.

The research-accept / paper-accept citation gate blocks UNREACHABLE + MISMATCH
citations. Real academic sources (publisher pages, OEIS behind Cloudflare,
KnotInfo, rate-limited registrars) frequently 403/401/429 an automated client —
the host EXISTS, it just gates the body. Classifying that as UNREACHABLE
false-flagged real references as fabricated and trapped projects at
research_review. These pin the access-gated -> PENDING (non-blocking, honestly
unverified) classification while keeping 404/DNS -> MISMATCH/UNREACHABLE (the
anti-fabrication gate is preserved).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents.tools import citation_fetcher as cf  # noqa: E402
from llmxive.types import VerificationStatus  # noqa: E402


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


def test_pending_does_not_block_the_gate():
    """A PENDING citation must NOT be counted by has_blocking_citations (only
    UNREACHABLE + MISMATCH block) — that's what makes access-gated refs advanceable.
    UNREACHABLE/MISMATCH still block (anti-fabrication gate intact)."""
    from types import SimpleNamespace

    from llmxive.agents.advancement import _has_blocking_citations
    pending = SimpleNamespace(verification_status=VerificationStatus.PENDING)
    unreachable = SimpleNamespace(verification_status=VerificationStatus.UNREACHABLE)
    assert _has_blocking_citations([pending]) is False
    assert _has_blocking_citations([pending, unreachable]) is True


def test_is_real_title_rejects_urls_dois_ids():
    assert cf._is_real_title("DynaCode: A Dynamic Complexity-Aware Code Benchmark") is True
    assert cf._is_real_title("https://doi.org/10.48550/arXiv.2503.10452") is False
    assert cf._is_real_title("10.48550/arXiv.2503.10452") is False
    assert cf._is_real_title("2503.10452") is False
    assert cf._is_real_title("") is False


def test_url_as_cited_title_does_not_false_mismatch():
    """The reference resolved to the REAL paper (fetched_title) but the citation
    stored a URL in cited_title — must be VERIFIED on existence, not MISMATCH."""
    out = cf._classify_match(
        "https://doi.org/10.48550/arXiv.2503.10452",        # cited_title is a URL
        "[2503.10452] DynaCode: A Dynamic Complexity-Aware Code Benchmark",  # real title
    )
    assert out == VerificationStatus.VERIFIED


def test_real_title_still_mismatches_when_unrelated():
    """A genuine cited title that doesn't match the fetched title still MISMATCHES
    (anti-fabrication intact)."""
    out = cf._classify_match("Attention Is All You Need", "Just a moment... | Cloudflare")
    assert out == VerificationStatus.MISMATCH


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
