"""Tests for the canonical 3-check verification helper (spec 005 / T014 / FR-003).

Real-HTTP tests where applicable. arXiv-backed tests have no key
dependency. Includes regression coverage of the spec-003 citation-
resolver behavior the librarian now subsumes.
"""

from __future__ import annotations

import os

import pytest

from llmxive.librarian.search import ArxivClient, Candidate
from llmxive.librarian.verify import (
    CITATION_TITLE_OVERLAP_THRESHOLD,
    SUMMARY_GROUNDING_THRESHOLD,
    VerificationFailure,
    VerifiedCitation,
    jaccard_tokens,
    verify_citation,
)

_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"

# The verify_citation tests resolve real arXiv URLs (and example.invalid),
# so they must skip outside real-call mode.
real_required = pytest.mark.skipif(
    not _REAL,
    reason="resolves real arXiv/HTTP URLs; needs LLMXIVE_REAL_TESTS=1",
)

# --- Tokenization + Jaccard ------------------------------------------------


def test_jaccard_identical_strings_score_one():
    assert jaccard_tokens("attention is all you need", "attention is all you need") == 1.0


def test_jaccard_disjoint_strings_score_zero():
    assert jaccard_tokens("foo bar baz", "qux quux corge") == 0.0


def test_jaccard_partial_overlap():
    """4 of 5 tokens overlap → 4/5 = 0.8."""
    score = jaccard_tokens("attention is all you need", "attention all you need")
    assert score == pytest.approx(0.8, abs=1e-6)


def test_jaccard_drops_short_tokens():
    """Single-letter tokens are dropped in tokenization."""
    # 'a' is dropped from both sides; 'b' is dropped; surviving tokens 'foo'/'bar' compare.
    s = jaccard_tokens("a foo b", "a bar b")
    assert s == 0.0  # foo vs bar share nothing


def test_jaccard_empty_input_yields_zero():
    assert jaccard_tokens("", "anything") == 0.0
    assert jaccard_tokens("anything", "") == 0.0


def test_jaccard_case_insensitive():
    assert jaccard_tokens("Attention", "ATTENTION") == 1.0


# --- verify_citation: real arXiv ------------------------------------------


@real_required
def test_known_good_arxiv_verifies():
    """Real Vaswani paper passes URL + title-overlap; summary grounded
    when the librarian's summary is derived from the abstract."""
    ax = ArxivClient(min_interval_seconds=0.5)
    candidate = ax.get_by_id("1706.03762")
    assert candidate is not None

    # A summary derived from the abstract → high overlap.
    summary = candidate.claimed_abstract or ""
    result = verify_citation(candidate, summary=summary)
    assert isinstance(result, VerifiedCitation), f"expected VerifiedCitation, got {type(result).__name__}"
    assert result.verification_log.url_resolves is True
    assert result.verification_log.title_token_overlap_score >= CITATION_TITLE_OVERLAP_THRESHOLD
    assert result.verification_log.summary_grounding_score >= SUMMARY_GROUNDING_THRESHOLD


@real_required
def test_known_bad_url_fails_with_url_not_resolves():
    """A primary_pointer pointing to a non-existent host returns a
    VerificationFailure with reason='url_not_resolves'."""
    bogus = Candidate(
        backend="arxiv",
        primary_pointer="https://example.invalid/never-existed",
        claimed_title="Made-up paper",
        claimed_authors=["Nobody"],
        claimed_year=2026,
        claimed_venue="Nowhere",
        claimed_abstract="Doesn't exist.",
    )
    result = verify_citation(bogus, summary="placeholder")
    assert isinstance(result, VerificationFailure)
    assert result.reason == "url_not_resolves"


@real_required
def test_title_mismatch_fails():
    """A candidate whose claimed title doesn't match the fetched title
    fails with reason='title_mismatch'."""
    ax = ArxivClient(min_interval_seconds=0.5)
    real = ax.get_by_id("1706.03762")
    # Mutate the candidate to claim a wildly different title.
    bogus = Candidate(
        backend=real.backend,
        primary_pointer=real.primary_pointer,
        claimed_title="Quantum Chromodynamics on Mars",
        claimed_authors=real.claimed_authors,
        claimed_year=real.claimed_year,
        claimed_venue=real.claimed_venue,
        claimed_abstract=real.claimed_abstract,
    )
    result = verify_citation(bogus, summary=real.claimed_abstract or "")
    assert isinstance(result, VerificationFailure)
    assert result.reason == "title_mismatch"
    # The score should have failed below threshold (≈ 0.0 here).
    assert "token-overlap" in result.details


@real_required
def test_summary_not_grounded_fails():
    """A candidate whose librarian-summary is unrelated to the abstract
    fails with reason='summary_not_grounded'."""
    ax = ArxivClient(min_interval_seconds=0.5)
    candidate = ax.get_by_id("1706.03762")
    # Pass a wildly off-topic summary.
    fake_summary = "This paper is about gardening tomatoes in tropical climates."
    result = verify_citation(candidate, summary=fake_summary)
    assert isinstance(result, VerificationFailure)
    assert result.reason == "summary_not_grounded"


@real_required
def test_verify_handles_missing_abstract_gracefully():
    """A candidate with no claimed_abstract still completes (URL +
    title checks pass; summary-grounding is a no-op)."""
    ax = ArxivClient(min_interval_seconds=0.5)
    real = ax.get_by_id("1706.03762")
    no_abstract = Candidate(
        backend=real.backend,
        primary_pointer=real.primary_pointer,
        claimed_title=real.claimed_title,
        claimed_authors=real.claimed_authors,
        claimed_year=real.claimed_year,
        claimed_venue=real.claimed_venue,
        claimed_abstract=None,
    )
    result = verify_citation(no_abstract, summary="")
    assert isinstance(result, VerifiedCitation)
    # URL resolved, title matched. Summary-grounding is 0 because both
    # sides were empty — but we DON'T fail when both sides are empty,
    # we just mark the score 0.
    assert result.verification_log.summary_grounding_score == 0.0


def test_direct_403_is_present_not_unreachable(monkeypatch):
    """A real host that 403s an automated client DIRECTLY (no redirect first —
    e.g. a publisher page, OEIS behind Cloudflare, KnotInfo) must classify as
    present_ambiguous (the reference EXISTS), NOT unreachable. The old code
    required a redirect chain and hard-blocked these real-but-bot-hostile refs."""
    import requests as _rq

    from llmxive.librarian import verify as _v

    class _Resp:
        status_code = 403
        url = "https://www.worldscientific.com/doi/abs/10.1142/X"
        history: list = []  # NO redirect

    monkeypatch.setattr(_v.requests, "head", lambda *a, **k: _Resp())
    out = _v.resolve_reference("url", "https://www.worldscientific.com/doi/abs/10.1142/X")
    assert out.state == "present_ambiguous", out
    assert out.present is True


def test_direct_404_is_still_unreachable(monkeypatch):
    """A 404 (resource does not exist) must STILL be unreachable — the
    anti-fabrication gate is preserved; only access-gating (401/403/429) is
    reclassified as present."""
    from llmxive.librarian import verify as _v

    class _Resp:
        status_code = 404
        url = "https://example.com/fabricated-path"
        history: list = []

    monkeypatch.setattr(_v.requests, "head", lambda *a, **k: _Resp())
    out = _v.resolve_reference("url", "https://example.com/fabricated-path")
    assert out.state == "unreachable", out
    assert out.present is False
