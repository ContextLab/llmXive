"""Tests for the PDF-sample audit (spec 005 / T016 / Q2).

Real-HTTP tests where applicable: the Vaswani arXiv PDF is the
reference test fixture. Per Constitution Principle III: no mocks.
"""

from __future__ import annotations

import os
import random

import pytest

from llmxive.librarian.pdf_sample import (
    PDFSampleResult,
    _extract_first_n_words,
    _pdf_url_for,
    annotate_with_pdf_sample,
    audit_pdf_grounding,
    select_pdf_sample,
)
from llmxive.librarian.search import ArxivClient
from llmxive.librarian.verify import VerificationLog, VerifiedCitation, verify_citation

_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"

# Downloads the real Vaswani arXiv PDF, so it skips outside real-call mode.
real_required = pytest.mark.skipif(
    not _REAL,
    reason="downloads a real arXiv PDF; needs LLMXIVE_REAL_TESTS=1",
)

# --- Sample-size selection -------------------------------------------------


def _make_vc(pointer: str) -> VerifiedCitation:
    """Cheap fixture: a VerifiedCitation with empty verification_log."""
    return VerifiedCitation(
        primary_pointer=pointer,
        bibliographic_info={"title": pointer, "authors": [], "year": None, "venue": None},
        summary="",
        summary_grounded_pdf=False,
        verification_log=VerificationLog(
            url_resolves=True, final_url=f"https://example.com/{pointer}",
            redirect_chain=[], http_status=200,
            title_token_overlap_score=1.0, summary_grounding_score=0.7,
            pdf_sample_score=None, verified_at="2026-05-06T12:00:00Z",
        ),
    )


def test_sample_size_min_one_when_verified_nonempty():
    """ceil(0.10 * len) with min 1: a list of 1-9 → exactly 1."""
    for n in range(1, 10):
        verified = [_make_vc(f"p{i}") for i in range(n)]
        sample = select_pdf_sample(verified, sample_rate=0.10)
        assert len(sample) == 1, f"len={n} → sample_size={len(sample)}, want 1"


def test_sample_size_at_ten_percent_for_larger_lists():
    """10 → 1; 11 → 2; 20 → 2; 50 → 5."""
    for n, expected in [(10, 1), (11, 2), (20, 2), (50, 5)]:
        verified = [_make_vc(f"p{i}") for i in range(n)]
        sample = select_pdf_sample(verified, sample_rate=0.10)
        assert len(sample) == expected, f"n={n}: got {len(sample)}, want {expected}"


def test_sample_size_zero_when_verified_empty():
    """Empty input → empty sample."""
    assert select_pdf_sample([], sample_rate=0.10) == []


def test_sample_is_random_seeded():
    """A fixed RNG seed produces deterministic sample selection."""
    verified = [_make_vc(f"p{i}") for i in range(50)]
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    s1 = select_pdf_sample(verified, sample_rate=0.10, rng=rng1)
    s2 = select_pdf_sample(verified, sample_rate=0.10, rng=rng2)
    assert [c.primary_pointer for c in s1] == [c.primary_pointer for c in s2]


# --- PDF URL inference -----------------------------------------------------


def test_pdf_url_for_bare_arxiv_id():
    vc = _make_vc("1706.03762")
    assert _pdf_url_for(vc) == "https://arxiv.org/pdf/1706.03762.pdf"


def test_pdf_url_for_arxiv_abs_url():
    vc = _make_vc("https://arxiv.org/abs/1706.03762")
    assert _pdf_url_for(vc) == "https://arxiv.org/pdf/1706.03762.pdf"


def test_pdf_url_for_https_pointer():
    vc = _make_vc("https://example.com/paper.pdf")
    assert _pdf_url_for(vc) == "https://example.com/paper.pdf"


def test_pdf_url_for_unrecognized_pointer():
    """Plain string with no scheme + not arXiv-shaped → None."""
    vc = _make_vc("ss-internal-id-xxx")
    assert _pdf_url_for(vc) is None


# --- Real PDF download + extraction ---------------------------------------


@real_required
def test_real_arxiv_pdf_extraction():
    """Vaswani PDF is downloadable + pypdf extracts ≥500 words of text."""
    ax = ArxivClient(min_interval_seconds=0.5)
    candidate = ax.get_by_id("1706.03762")
    summary = candidate.claimed_abstract or ""
    verified = verify_citation(candidate, summary=summary)
    assert isinstance(verified, VerifiedCitation)

    audit = audit_pdf_grounding(verified)
    assert isinstance(audit, PDFSampleResult)
    # Expect successful audit (failure_reason is None).
    assert audit.failure_reason is None, f"expected success, got: {audit.failure_reason}"
    # PDF was sampled; result is True or False (not None).
    assert audit.summary_grounded_pdf in (True, False)
    assert audit.pdf_sample_score is not None
    assert 0.0 <= audit.pdf_sample_score <= 1.0


def test_extract_first_n_words_handles_empty_bytes():
    """Empty bytes yield empty string (graceful)."""
    assert _extract_first_n_words(b"", n=100) == ""


def test_extract_first_n_words_handles_garbage_bytes():
    """Garbage bytes (not a PDF) yield empty string (graceful)."""
    assert _extract_first_n_words(b"this is not a pdf at all", n=100) == ""


# --- annotate_with_pdf_sample --------------------------------------------


def test_annotate_marks_sampled_subset_only():
    """Verified citations in the sample get the audit flag; others stay False."""
    verified = [_make_vc(f"p{i}") for i in range(5)]
    # Pretend we sampled p0 + p2; both passed.
    sample_results = [
        PDFSampleResult(
            primary_pointer="p0",
            summary_grounded_pdf=True,
            pdf_sample_score=0.85,
            failure_reason=None,
        ),
        PDFSampleResult(
            primary_pointer="p2",
            summary_grounded_pdf=False,  # PDF sample disagreed
            pdf_sample_score=0.30,
            failure_reason=None,
        ),
    ]
    annotated = annotate_with_pdf_sample(verified, sample_results)
    by_id = {v.primary_pointer: v for v in annotated}
    assert by_id["p0"].summary_grounded_pdf is True
    assert by_id["p0"].verification_log.pdf_sample_score == 0.85
    assert by_id["p2"].summary_grounded_pdf is False
    assert by_id["p2"].verification_log.pdf_sample_score == 0.30
    # Unsampled stay at False (per E3 — "False if abstract-only verification
    # passed but not PDF-sampled").
    for unsampled in ("p1", "p3", "p4"):
        assert by_id[unsampled].summary_grounded_pdf is False
        assert by_id[unsampled].verification_log.pdf_sample_score is None


def test_annotate_handles_paywall_inaccessible():
    """A paywalled PDF audit gets summary_grounded_pdf=None."""
    verified = [_make_vc("p0")]
    sample_results = [
        PDFSampleResult(
            primary_pointer="p0",
            summary_grounded_pdf=None,  # inaccessible
            pdf_sample_score=None,
            failure_reason="paywall_or_forbidden_403",
        )
    ]
    annotated = annotate_with_pdf_sample(verified, sample_results)
    assert annotated[0].summary_grounded_pdf is None
    assert annotated[0].verification_log.pdf_sample_score is None
