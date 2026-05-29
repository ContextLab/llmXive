"""Topical-relevance gate tests (spec 005 fix).

The earlier verify_citation chain only compared backend metadata
against itself (claimed_title vs fetched_title), so SS + arXiv hits
that shared only generic stop-tokens with the user's query slipped
through. The relevance gate (Check 0) filters those out at the
metadata stage, before any HTTP work.

Concrete failure mode caught:
  query="How does gut microbiome composition relate to cognitive
  performance in aging individuals, after controlling for lifestyle and
  demographic confounders"
  candidate.claimed_title="Demographic Confounding Causes Extreme
  Instances of Lifestyle Politics on Facebook"
  → previously verified; now correctly rejected as query_irrelevant.
"""

from __future__ import annotations

import os

import pytest

from llmxive.librarian.search import Candidate
from llmxive.librarian.verify import (
    QUERY_RELEVANCE_THRESHOLD,
    VerificationFailure,
    query_relevance_score,
    verify_citation,
)

_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"

# This test passes no query, so verify_citation moves past the metadata
# gate and attempts real URL resolution — skip it outside real-call mode.
real_required = pytest.mark.skipif(
    not _REAL,
    reason="attempts real URL resolution; needs LLMXIVE_REAL_TESTS=1",
)

# --- Pure-function tests (no HTTP) -------------------------------------------


def test_relevance_score_above_threshold_for_topical_match() -> None:
    query = "graph neural networks for molecular property prediction"
    candidate_text = (
        "Graph Neural Networks for Predicting Molecular Properties: "
        "A Comprehensive Survey of GNN Architectures."
    )
    score = query_relevance_score(query, candidate_text)
    assert score >= QUERY_RELEVANCE_THRESHOLD, (
        f"score={score} should be ≥ {QUERY_RELEVANCE_THRESHOLD} for topical match"
    )


def test_relevance_score_below_threshold_for_off_topic() -> None:
    """The actual concrete bug: gut-microbiome query, Facebook-politics paper."""
    query = (
        "How does gut microbiome taxonomic composition relate to "
        "cognitive performance in aging individuals, after controlling for "
        "lifestyle and demographic confounders"
    )
    candidate_text = (
        "Demographic Confounding Causes Extreme Instances of Lifestyle "
        "Politics on Facebook"
    )
    score = query_relevance_score(query, candidate_text)
    assert score < QUERY_RELEVANCE_THRESHOLD, (
        f"score={score} should be < {QUERY_RELEVANCE_THRESHOLD} for off-topic"
    )


def test_relevance_score_handles_empty_inputs() -> None:
    assert query_relevance_score("", "anything") == 0.0
    assert query_relevance_score("query", "") == 0.0
    assert query_relevance_score("", "") == 0.0


def test_relevance_score_filters_stop_tokens() -> None:
    """A candidate that overlaps with the query ONLY on stop-tokens
    (the/and/of/study/etc.) should score 0."""
    query = "the study of the effects of the analysis of the methods"
    candidate_text = "the study of the analysis of the the the"
    score = query_relevance_score(query, candidate_text)
    # All overlap is stop-tokens; salient query tokens = empty after filter.
    assert score == 0.0


# --- verify_citation integration test (no HTTP — short-circuits on Check 0) --


def test_verify_citation_rejects_query_irrelevant_candidate() -> None:
    """End-to-end: bogus candidate gets rejected before HTTP fires."""
    bogus = Candidate(
        backend="semantic_scholar",
        primary_pointer="https://example.invalid/never-fetched",
        claimed_title="Demographic Confounding Causes Extreme Instances of Lifestyle Politics on Facebook",
        claimed_authors=["A. Author"],
        claimed_year=2022,
        claimed_venue=None,
        claimed_abstract="A study of demographic patterns in social media activity.",
    )
    query = (
        "How does gut microbiome taxonomic composition relate to "
        "cognitive performance in aging individuals"
    )
    result = verify_citation(bogus, summary=bogus.claimed_abstract or "", query=query)
    assert isinstance(result, VerificationFailure)
    assert result.reason == "query_irrelevant"
    assert "query-relevance" in result.details


@real_required
def test_verify_citation_no_query_disables_gate() -> None:
    """Backward-compat: callers not passing `query` skip the gate. We
    verify by constructing a candidate whose URL would 404 (proving we
    move past Check 0 to Check 1 = url_not_resolves)."""
    bogus = Candidate(
        backend="semantic_scholar",
        primary_pointer="https://example.invalid/never-resolves",
        claimed_title="Anything",
        claimed_authors=[],
        claimed_year=None,
        claimed_venue=None,
        claimed_abstract=None,
    )
    # No query arg — gate disabled. URL fails check 1.
    result = verify_citation(bogus, summary="")
    assert isinstance(result, VerificationFailure)
    assert result.reason == "url_not_resolves"
