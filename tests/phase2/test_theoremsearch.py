"""Tests for the TheoremSearch backend client (spec 006 / FR-A01..A06).

Parser + Candidate-mapping + dedup + failure-handling tests against the
recorded `/search` fixtures, plus a real-API smoke test gated on network
reachability so CI without outbound HTTP still passes.

Per Constitution Principle III: the offline tests stub only the HTTP
layer (`requests.post`) and the arXiv resolver (`ArxivClient.get_by_id`)
— everything else (parsing, dedup, the `TransientBackendError` →
empty-list fall-through) exercises the real code paths. The gated smoke
test hits the live API.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
import requests

from llmxive.agents.librarian import _theoremsearch_candidates
from llmxive.backends.base import TransientBackendError
from llmxive.librarian.search import Candidate
from llmxive.librarian.theoremsearch import API_URL, TheoremSearchClient

_FIXTURES = Path(__file__).parent / "fixtures"
_SEARCH_FIXTURE = _FIXTURES / "theoremsearch_search_response.json"
_PROOFWIKI_FIXTURE = _FIXTURES / "theoremsearch_proofwiki_response.json"


# --- test doubles ---------------------------------------------------------


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, body=None, raise_on_json: bool = False):
        self.status_code = status_code
        self._body = body
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("not JSON")
        return self._body


class _StubArxiv:
    """Stand-in for ArxivClient.get_by_id: returns a Candidate for known
    ids, ``None`` for ids in ``missing``.
    """

    def __init__(self, *, missing: set[str] | None = None, normalize: dict[str, str] | None = None):
        self._missing = missing or set()
        self._normalize = normalize or {}
        self.calls: list[str] = []

    def get_by_id(self, arxiv_id: str) -> Candidate | None:
        self.calls.append(arxiv_id)
        if arxiv_id in self._missing:
            return None
        pointer = self._normalize.get(arxiv_id, arxiv_id)
        return Candidate(
            backend="arxiv",
            primary_pointer=pointer,
            claimed_title=f"Resolved title for {arxiv_id}",
            claimed_authors=["A. Author", "B. Coauthor"],
            claimed_year=2020,
            claimed_venue="arXiv",
            claimed_abstract=f"Abstract resolved from arXiv for {arxiv_id}.",
        )


def _load(fixture: Path) -> dict:
    return json.loads(fixture.read_text(encoding="utf-8"))


def _patch_post(monkeypatch, *, body=None, status_code: int = 200, raise_exc=None, raise_on_json=False):
    captured: dict = {}

    def _fake_post(url, *, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        if raise_exc is not None:
            raise raise_exc
        return _FakeResponse(status_code=status_code, body=body, raise_on_json=raise_on_json)

    monkeypatch.setattr(requests, "post", _fake_post)
    return captured


# --- T020: parser / Candidate-mapping / dedup -----------------------------


def test_search_maps_arxiv_hits_to_candidates(monkeypatch) -> None:
    body = _load(_SEARCH_FIXTURE)
    captured = _patch_post(monkeypatch, body=body)
    stub = _StubArxiv()
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)

    out = client.search("sharp bound spectral gap random regular graphs", limit=8)

    # Posted to the right endpoint with {query, limit}.
    assert captured["url"] == API_URL
    assert captured["json"] == {
        "query": "sharp bound spectral gap random regular graphs",
        "limit": 8,
    }
    # The fixture is 10 arXiv-sourced hits — each resolved to a Candidate
    # re-tagged backend="theoremsearch".
    assert out, "expected at least one resolved candidate"
    assert all(isinstance(c, Candidate) for c in out)
    assert all(c.backend == "theoremsearch" for c in out)
    assert all(c.claimed_venue == "arXiv" for c in out)
    assert all(c.claimed_abstract for c in out)  # abstract needed by the grounding check
    # primary_pointer comes from the resolver (version stripped at resolve time
    # — the stub echoes the stripped id we pass it).
    assert "1306.5434v2" not in {c.primary_pointer for c in out}
    assert "1306.5434" in {c.primary_pointer for c in out}


def test_search_skips_non_arxiv_sources(monkeypatch) -> None:
    body = _load(_PROOFWIKI_FIXTURE)
    _patch_post(monkeypatch, body=body)
    stub = _StubArxiv()
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)

    out = client.search("every finite group has a composition series", limit=3)

    # Fixture has ProofWiki + arXiv hits; ProofWiki must be dropped, and
    # `1210.7958v1` appears twice → one Candidate. Distinct arXiv ids:
    # 2303.01957, 1210.7958, 2503.09177, math/0503154, 0911.5433 → 5.
    assert len(out) == 5
    pointers = {c.primary_pointer for c in out}
    assert pointers == {"2303.01957", "1210.7958", "2503.09177", "math/0503154", "0911.5433"}
    assert all(c.backend == "theoremsearch" for c in out)
    # The resolver was never asked about the ProofWiki "paper_id" "proofwiki".
    assert "proofwiki" not in stub.calls


def test_search_strips_version_suffix_before_resolving(monkeypatch) -> None:
    body = _load(_SEARCH_FIXTURE)
    _patch_post(monkeypatch, body=body)
    stub = _StubArxiv()
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)

    client.search("anything", limit=8)

    # Every id handed to get_by_id has no trailing vN.
    assert stub.calls, "resolver should have been called"
    assert all(not c.endswith(("v1", "v2", "v3", "v4", "v5", "v6")) for c in stub.calls), stub.calls


def test_search_dedups_within_call(monkeypatch) -> None:
    # Two hits → same arXiv id → one Candidate (the ProofWiki fixture has
    # 1210.7958v1 twice).
    body = _load(_PROOFWIKI_FIXTURE)
    _patch_post(monkeypatch, body=body)
    stub = _StubArxiv()
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)

    out = client.search("dup test", limit=3)
    pointers = [c.primary_pointer for c in out]
    assert len(pointers) == len(set(pointers)), pointers
    assert pointers.count("1210.7958") == 1


def test_unresolvable_arxiv_id_produces_no_candidate(monkeypatch) -> None:
    body = _load(_SEARCH_FIXTURE)
    _patch_post(monkeypatch, body=body)
    # Make the FIRST hit's id unresolvable; the rest still resolve.
    stub = _StubArxiv(missing={"1306.5434"})
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)

    out = client.search("anything", limit=8)
    assert "1306.5434" not in {c.primary_pointer for c in out}
    assert out, "the other hits should still produce candidates"


def test_empty_term_returns_empty_without_http(monkeypatch) -> None:
    called = {"n": 0}

    def _boom(*a, **k):  # pragma: no cover — must not be reached
        called["n"] += 1
        raise AssertionError("HTTP should not be called for an empty term")

    monkeypatch.setattr(requests, "post", _boom)
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=_StubArxiv())
    assert client.search("   ", limit=5) == []
    assert called["n"] == 0


def test_search_orders_by_score_descending(monkeypatch) -> None:
    # Build a tiny synthetic body with out-of-order scores; assert the
    # first-resolved candidate corresponds to the highest score.
    body = {
        "theorems": [
            {"paper": {"source": "arXiv", "paper_id": "2001.00001"}, "score": 0.1},
            {"paper": {"source": "arXiv", "paper_id": "2002.00002"}, "score": 0.9},
            {"paper": {"source": "arXiv", "paper_id": "2003.00003"}, "score": 0.5},
        ]
    }
    _patch_post(monkeypatch, body=body)
    stub = _StubArxiv()
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=stub)
    out = client.search("scores", limit=10)
    assert [c.primary_pointer for c in out] == ["2002.00002", "2003.00003", "2001.00001"]


# --- T021: failure handling + the librarian wrapper -----------------------


@pytest.mark.parametrize(
    "kw",
    [
        {"status_code": 500},
        {"status_code": 404},
        {"raise_exc": requests.ConnectionError("dns")},
        {"raise_exc": requests.Timeout("slow")},
        {"raise_on_json": True},
    ],
)
def test_search_raises_transient_on_http_or_network_or_nonjson(monkeypatch, kw) -> None:
    body = _load(_SEARCH_FIXTURE) if not kw.get("raise_on_json") else "not-json"
    _patch_post(monkeypatch, body=body, **kw)
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=_StubArxiv())
    with pytest.raises(TransientBackendError):
        client.search("x", limit=5)


def test_search_raises_transient_on_missing_theorems_array(monkeypatch) -> None:
    _patch_post(monkeypatch, body={"results": []})  # wrong key
    client = TheoremSearchClient(min_interval_seconds=0.0, arxiv_client=_StubArxiv())
    with pytest.raises(TransientBackendError):
        client.search("x", limit=5)


def test_librarian_wrapper_swallows_transient_and_returns_empty(monkeypatch) -> None:
    """`_theoremsearch_candidates` (the wrapper in librarian.py) must turn
    a TheoremSearch outage into [] so the librarian completes on SS+arXiv.
    """
    _patch_post(monkeypatch, body=None, status_code=503)

    class _AnyArxiv:
        def get_by_id(self, _id):  # pragma: no cover — never reached
            return None

    out = _theoremsearch_candidates("some math question", arxiv_client=_AnyArxiv())
    assert out == []


# --- real-API smoke (gated on outbound network) ---------------------------


def _network_reachable(host: str = "api.theoremsearch.com", port: int = 443, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not _network_reachable(), reason="api.theoremsearch.com not reachable")
def test_real_api_smoke() -> None:
    client = TheoremSearchClient()  # real ArxivClient, real HTTP
    out = client.search("sharp bound spectral gap random regular graphs", limit=5)
    # The API + arXiv resolver should yield ≥1 usable candidate; if the
    # API returned only non-arXiv hits this run we still don't fail (a
    # zero-arXiv-hit response is a documented normal outcome) — but assert
    # the shape of whatever came back.
    assert isinstance(out, list)
    for c in out:
        assert c.backend == "theoremsearch"
        assert c.claimed_venue == "arXiv"
        assert c.primary_pointer and not c.primary_pointer.endswith(("v1", "v2", "v3"))
        assert c.claimed_abstract


# --- librarian-level wiring smoke (gated on the real backends) ------------


def _real_librarian_ready() -> bool:
    try:
        from llmxive.credentials import load_dartmouth_key, load_semantic_scholar_key
    except Exception:  # pragma: no cover
        return False
    return (
        bool(load_dartmouth_key(prompt_if_missing=False))
        and bool(load_semantic_scholar_key(prompt_if_missing=False))
        and _network_reachable()
    )


@pytest.mark.skipif(
    not _real_librarian_ready(),
    reason="needs DARTMOUTH_CHAT_API_KEY + SEMANTIC_SCHOLAR_API_KEY + network",
)
def test_librarian_statistics_field_triggers_theoremsearch_unconditionally(tmp_path) -> None:
    """`field="statistics"` → TheoremSearch is queried WITHOUT consulting
    the math-classifier; the audit object is the unconditional-trigger
    shape; the wiring runs without error.
    """
    from llmxive.agents import registry
    from llmxive.agents.librarian import LibrarianAgent

    librarian = LibrarianAgent(registry.get("librarian"))
    result = librarian.invoke(
        term=(
            "what is the tightest known concentration inequality for sums of "
            "bounded independent random variables, and where is it proved?"
        ),
        field="statistics",
        target_n=3,
        repo_root=tmp_path,
        no_cache=True,
    )
    d = result.to_dict()
    assert d["math_classifier"] == {"invoked": False, "verdict": None, "error": None}
    assert d["outcome"] != "failed"
    # If TheoremSearch contributed anything this run it shows up tagged in
    # the verification log; a zero-hit run is tolerated (the API may have
    # returned only non-arXiv hits or been briefly unavailable).
    backends = {
        (v.get("verification_log") or {}).get("backend")
        for v in d["verified_citations"]
    }
    assert "theoremsearch" in backends or len(d["verified_citations"]) >= 1
