"""Real-API tests for the librarian search clients (spec 005 / T013 / FR-001).

Per Constitution Principle III: real HTTP, no mocks. Per Q1: Semantic
Scholar Graph API + arXiv API only.

Tests requiring the SS API key are marked
``@pytest.mark.skipif(not has_ss_key)`` so they skip cleanly when the
key is missing. arXiv tests have no key dependency.
"""

from __future__ import annotations

import time

import pytest

from llmxive.credentials import load_semantic_scholar_key
from llmxive.librarian.search import (
    ArxivClient,
    Candidate,
    SemanticScholarClient,
    _TokenBucket,
    merge_candidates,
)

HAS_SS_KEY = bool(load_semantic_scholar_key(prompt_if_missing=False))
ss_required = pytest.mark.skipif(
    not HAS_SS_KEY,
    reason="SEMANTIC_SCHOLAR_API_KEY not set; SS-backed tests require the key",
)


# --- Token bucket -----------------------------------------------------------


def test_token_bucket_burst_then_replenish():
    """Burst capacity is consumed immediately; subsequent acquires wait."""
    b = _TokenBucket(capacity=2, replenish_rate=10.0)  # 10/sec
    t0 = time.monotonic()
    b.acquire()
    b.acquire()
    burst_dt = time.monotonic() - t0
    assert burst_dt < 0.05, f"2 acquires from full bucket should be ~instant, got {burst_dt:.3f}s"

    # Third acquire must wait for replenishment (~100ms at 10/sec).
    t1 = time.monotonic()
    b.acquire()
    wait_dt = time.monotonic() - t1
    assert 0.05 < wait_dt < 0.3, f"3rd acquire should wait ~100ms; got {wait_dt:.3f}s"


def test_token_bucket_thread_safe():
    """Concurrent acquires don't double-consume."""
    import threading

    b = _TokenBucket(capacity=5, replenish_rate=100.0)  # generous
    counts = []

    def worker():
        b.acquire()
        counts.append(1)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(counts) == 10  # all 10 succeeded; no double-consumes



# --- arXiv client (no key required) ----------------------------------------


def test_arxiv_get_by_id_real():
    """Fetching a known arXiv paper by ID returns the right metadata."""
    ax = ArxivClient(min_interval_seconds=0.5)
    candidate = ax.get_by_id("1706.03762")
    assert candidate is not None
    assert "Attention" in candidate.claimed_title
    assert candidate.claimed_year == 2017
    assert candidate.backend == "arxiv"
    assert candidate.primary_pointer == "1706.03762"
    assert any("Vaswani" in a for a in candidate.claimed_authors)
    assert candidate.claimed_abstract is not None and len(candidate.claimed_abstract) > 100


def test_arxiv_search_real():
    """Keyword search returns ≥1 candidate for a well-known query."""
    ax = ArxivClient(min_interval_seconds=0.5)
    results = ax.search("attention is all you need transformer", max_results=3)
    assert len(results) >= 1, f"expected ≥1 hit, got {len(results)}"
    for c in results:
        assert c.backend == "arxiv"
        assert c.primary_pointer
        assert c.claimed_title


def test_arxiv_search_empty_query_returns_empty():
    """An empty query short-circuits without hitting the API."""
    ax = ArxivClient(min_interval_seconds=0.5)
    assert ax.search("", max_results=3) == []
    assert ax.search("   ", max_results=3) == []


# --- Semantic Scholar client (key required) --------------------------------


@ss_required
def test_ss_search_real():
    """Authenticated SS search returns ≥1 candidate for a known query."""
    ss = SemanticScholarClient()
    assert ss.has_key, "SS key should be loaded before running this test"
    results = ss.search_papers("transformer attention", limit=3)
    assert len(results) >= 1, f"expected ≥1 hit; got {len(results)}"
    for c in results:
        assert c.backend == "semantic_scholar"
        assert c.primary_pointer
        assert c.claimed_title


@ss_required
def test_ss_search_empty_query_returns_empty():
    """Empty query short-circuits."""
    ss = SemanticScholarClient()
    assert ss.search_papers("", limit=3) == []


@ss_required
def test_ss_search_uses_x_api_key_header():
    """The client adds the x-api-key header when a key is present."""
    ss = SemanticScholarClient()
    headers = ss._headers()  # noqa: SLF001 — testing internal header construction
    assert "x-api-key" in headers
    assert headers["x-api-key"] == load_semantic_scholar_key()


def test_ss_client_without_key_raises_on_search():
    """If no key is present, search_papers raises a clear error."""
    ss = SemanticScholarClient(api_key="")  # explicit empty
    with pytest.raises(RuntimeError, match="SEMANTIC_SCHOLAR_API_KEY missing"):
        ss.search_papers("anything")


# --- merge_candidates ------------------------------------------------------


def test_merge_candidates_dedups_by_identity():
    """Same (backend, primary_pointer) appears once in the merged list."""
    a = Candidate(
        backend="arxiv",
        primary_pointer="1706.03762",
        claimed_title="A",
        claimed_authors=[],
        claimed_year=2017,
        claimed_venue=None,
        claimed_abstract=None,
    )
    a_dup = Candidate(
        backend="arxiv",
        primary_pointer="1706.03762",
        claimed_title="A (duplicate)",
        claimed_authors=[],
        claimed_year=2017,
        claimed_venue=None,
        claimed_abstract=None,
    )
    b = Candidate(
        backend="semantic_scholar",
        primary_pointer="1706.03762",  # same pointer, different backend
        claimed_title="B",
        claimed_authors=[],
        claimed_year=2017,
        claimed_venue=None,
        claimed_abstract=None,
    )
    merged = merge_candidates([a, a_dup], [b])
    # arxiv-1706.03762 is one identity; ss-1706.03762 is a different identity.
    assert len(merged) == 2
    assert {(c.backend, c.primary_pointer) for c in merged} == {
        ("arxiv", "1706.03762"),
        ("semantic_scholar", "1706.03762"),
    }


def test_merge_candidates_preserves_first_seen_order():
    """First occurrence of each identity wins."""
    a1 = Candidate(
        backend="arxiv", primary_pointer="x", claimed_title="first",
        claimed_authors=[], claimed_year=None, claimed_venue=None, claimed_abstract=None,
    )
    a2 = Candidate(
        backend="arxiv", primary_pointer="x", claimed_title="second",
        claimed_authors=[], claimed_year=None, claimed_venue=None, claimed_abstract=None,
    )
    merged = merge_candidates([a1], [a2])
    assert len(merged) == 1
    assert merged[0].claimed_title == "first"  # first-seen wins
