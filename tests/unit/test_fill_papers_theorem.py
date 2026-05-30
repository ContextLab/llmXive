"""T017: Unit tests for fill/channels/papers.py + theorem.py.

Tests the pure candidate→FetchedSource adaptation helper.
Network parts are gated behind LLMXIVE_REAL_TESTS.
"""

from __future__ import annotations

import os

import pytest

from llmxive.fill.channels.papers import _candidate_to_source
from llmxive.fill.channels.theorem import _candidate_to_source as theorem_candidate_to_source
from llmxive.fill.channels import AUTHORITY
from llmxive.fill.models import FetchedSource
from llmxive.librarian.search import Candidate
from llmxive.grounding.full_text import RetrievedDoc
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus


def _make_claim() -> Claim:
    return Claim(
        claim_id="c_test0001",
        kind=ClaimKind.NUMERIC,
        raw_text="There are 9988 prime knots at 13 crossings.",
        canonical="9988",
        context="prime knots at 13 crossings",
        artifact_path="test/artifact.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence={},
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
        source_hash=None,
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_candidate(pointer: str = "2301.12345", title: str = "Test Paper") -> Candidate:
    return Candidate(
        backend="semantic_scholar",
        primary_pointer=pointer,
        claimed_title=title,
        claimed_authors=["Author A"],
        claimed_year=2023,
        claimed_venue="ArXiv",
        claimed_abstract="Abstract text here.",
    )


def _make_doc(full_text: str | None = "Full text of the paper.", abstract: str | None = None) -> RetrievedDoc:
    return RetrievedDoc(
        kind="arxiv",
        value="2301.12345",
        tier="arxiv",
        full_text=full_text,
        abstract=abstract,
        title="Test Paper",
        final_url="https://arxiv.org/abs/2301.12345",
        error=None,
    )


# ---------------------------------------------------------------------------
# papers._candidate_to_source
# ---------------------------------------------------------------------------

class TestPaperCandidateToSource:
    def test_basic_with_full_text(self):
        candidate = _make_candidate()
        doc = _make_doc(full_text="The prime knot count at 13 crossings is 9988.")
        result = _candidate_to_source(candidate, doc)
        assert isinstance(result, FetchedSource)
        assert result.channel == "paper"
        assert result.authority == AUTHORITY["paper"]
        assert result.text == "The prime knot count at 13 crossings is 9988."
        assert result.url == "https://arxiv.org/abs/2301.12345"
        assert result.title == "Test Paper"
        assert result.source_id == "2301.12345"

    def test_falls_back_to_abstract(self):
        candidate = _make_candidate()
        doc = _make_doc(full_text=None, abstract="Abstract: 9988 prime knots.")
        result = _candidate_to_source(candidate, doc)
        assert result is not None
        assert result.text == "Abstract: 9988 prime knots."

    def test_returns_none_when_unreadable(self):
        candidate = _make_candidate()
        doc = _make_doc(full_text=None, abstract=None)
        result = _candidate_to_source(candidate, doc)
        assert result is None

    def test_prefers_full_text_over_abstract(self):
        candidate = _make_candidate()
        doc = _make_doc(full_text="Full text.", abstract="Abstract.")
        result = _candidate_to_source(candidate, doc)
        assert result.text == "Full text."

    def test_source_id_from_pointer(self):
        candidate = _make_candidate(pointer="10.1234/some-doi")
        doc = _make_doc()
        result = _candidate_to_source(candidate, doc)
        assert result.source_id == "10.1234/some-doi"


# ---------------------------------------------------------------------------
# theorem._candidate_to_source
# ---------------------------------------------------------------------------

class TestTheoremCandidateToSource:
    def test_basic(self):
        candidate = Candidate(
            backend="theoremsearch",
            primary_pointer="2301.12345",
            claimed_title="A Theorem Paper",
            claimed_authors=["Euler"],
            claimed_year=2023,
            claimed_venue=None,
            claimed_abstract="About theorems.",
        )
        doc = _make_doc(full_text="Theorem content here.")
        result = theorem_candidate_to_source(candidate, doc)
        assert isinstance(result, FetchedSource)
        assert result.channel == "theorem"
        assert result.authority == AUTHORITY["theorem"]
        assert result.text == "Theorem content here."

    def test_returns_none_when_unreadable(self):
        candidate = Candidate(
            backend="theoremsearch",
            primary_pointer="2301.12345",
            claimed_title="Empty",
            claimed_authors=[],
            claimed_year=None,
            claimed_venue=None,
            claimed_abstract=None,
        )
        doc = _make_doc(full_text=None, abstract=None)
        result = theorem_candidate_to_source(candidate, doc)
        assert result is None


# ---------------------------------------------------------------------------
# Real-call gated tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="LLMXIVE_REAL_TESTS not set",
)
def test_papers_search_and_fetch_real():
    from llmxive.fill.channels.papers import search_and_fetch

    claim = _make_claim()
    results = search_and_fetch("prime knots crossing number knot theory", claim)
    assert isinstance(results, list)
    # May return [] if SS key not available or network down; just check type
    for src in results:
        assert isinstance(src, FetchedSource)
        assert src.channel == "paper"
        assert src.text


@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="LLMXIVE_REAL_TESTS not set",
)
def test_theorem_search_and_fetch_real():
    from llmxive.fill.channels.theorem import search_and_fetch

    claim = _make_claim()
    results = search_and_fetch("prime knots crossing number", claim)
    assert isinstance(results, list)
    for src in results:
        assert isinstance(src, FetchedSource)
        assert src.channel == "theorem"
        assert src.text
