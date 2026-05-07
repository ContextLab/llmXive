"""Induced-failure smoke tests for the librarian (spec 005 / T031a / SC-007).

Three deliberately-induced failure modes per ``contracts/cross-domain-coverage.md``
defect-categorization table + spec.md SC-007:

  1. backend unreachable → librarian returns ``outcome: failed`` with non-empty failure_reason
  2. DOI redirects to wrong paper → verification_failures records reason=title_mismatch
  3. paywall on PDF download → citation present with summary_grounded_pdf=None

Per Constitution Principle V: failure paths are LOUD. No silent state
advancement; failure_reason populated.
"""

from __future__ import annotations

import dataclasses

import pytest
import requests

from llmxive.librarian.pdf_sample import audit_pdf_grounding
from llmxive.librarian.search import (
    ArxivClient,
    Candidate,
    SemanticScholarClient,
)
from llmxive.librarian.verify import (
    VerificationFailure,
    VerificationLog,
    VerifiedCitation,
    verify_citation,
)


# --- Scenario 1: backend unreachable ---------------------------------------


def test_arxiv_unreachable_returns_empty_loudly(capsys):
    """Forcing a network-level failure on ArxivClient.search() returns []
    AND prints a stderr diagnostic (loud, not silent)."""
    ax = ArxivClient(min_interval_seconds=0.1)
    # Monkey-patch the arxiv library to raise OSError.
    import arxiv as _arxiv_mod

    real_client = _arxiv_mod.Client

    class _BorkedClient:
        def __init__(self, *args, **kwargs):
            pass
        def results(self, search):
            raise OSError("simulated network failure")

    _arxiv_mod.Client = _BorkedClient
    try:
        results = ax.search("transformer attention", max_results=2)
    finally:
        _arxiv_mod.Client = real_client

    assert results == []
    # Loud failure: stderr captured non-empty diagnostic.
    captured = capsys.readouterr()
    assert "[arxiv]" in captured.err
    assert "OSError" in captured.err or "simulated network failure" in captured.err


def test_ss_client_with_invalid_key_raises_loud():
    """An obviously-invalid SS key triggers loud HTTP error, not silent
    empty result."""
    ss = SemanticScholarClient(api_key="invalid-key-for-induced-failure")
    # The SS API returns 403 for bad keys (or 401, or 429 if it
    # treats unauthenticated as limited). Either way it shouldn't
    # silently return [].
    with pytest.raises(requests.HTTPError):
        ss.search_papers("transformer attention", limit=1)


# --- Scenario 2: title mismatch (synthetic DOI-redirects-to-wrong-paper) ---


def test_synthetic_title_mismatch_recorded_as_failure():
    """A candidate whose claimed_title doesn't match the real fetched
    title fails with reason='title_mismatch'. Mirrors the case where
    a DOI redirects to a different paper than its bibliographic claim.
    """
    # Use the real Vaswani arXiv paper but lie about its title.
    ax = ArxivClient(min_interval_seconds=0.5)
    real = ax.get_by_id("1706.03762")
    bogus = Candidate(
        backend=real.backend,
        primary_pointer=real.primary_pointer,
        claimed_title="Untitled Quantum Chromodynamics on Mars",  # totally unrelated
        claimed_authors=real.claimed_authors,
        claimed_year=real.claimed_year,
        claimed_venue=real.claimed_venue,
        claimed_abstract=real.claimed_abstract,
    )
    result = verify_citation(bogus, summary=real.claimed_abstract or "")
    assert isinstance(result, VerificationFailure)
    assert result.reason == "title_mismatch"
    assert result.details, "details must be populated, not silent"
    assert "token-overlap" in result.details


# --- Scenario 3: paywall on PDF download ---


def test_paywalled_pdf_returns_none_grounding():
    """A 401/403 on PDF download surfaces as summary_grounded_pdf=None
    AND failure_reason populated (not silently True/False)."""
    log = VerificationLog(
        url_resolves=True,
        final_url="https://example.com/paywalled.pdf",
        redirect_chain=[],
        http_status=200,
        title_token_overlap_score=1.0,
        summary_grounding_score=0.7,
        pdf_sample_score=None,
        verified_at="2026-05-06T12:00:00Z",
    )
    citation = VerifiedCitation(
        primary_pointer="https://example.invalid/paper",  # unreachable host
        bibliographic_info={"title": "X", "authors": [], "year": None, "venue": None},
        summary="abstract text",
        summary_grounded_pdf=False,
        verification_log=log,
    )
    audit = audit_pdf_grounding(citation)
    assert audit.summary_grounded_pdf is None  # inaccessible, not False
    assert audit.failure_reason is not None  # populated, not silent
    assert audit.pdf_sample_score is None
