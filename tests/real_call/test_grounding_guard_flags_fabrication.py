"""Real-call (LLMXIVE_REAL_TESTS=1) tests for the F-19 factual-grounding guard.

F-19 closes the gap F-18 left open. F-18 verifies a reference RESOLVES; F-19
verifies the cited source SUBSTANTIATES the claim/number attached to it. The
PROJ-552 fabrication cascade exploited the gap: the reviser "resolved" a
(correct) knot count by FABRICATING a wrong number (1,296) on a free-text
author-year citation ("Kauffman & Lambropoulou 2004"), and the panel PASSED it.

These tests make REAL calls (arXiv API for grounding; Dartmouth LLM for the
orchestrator's extraction) — gated behind LLMXIVE_REAL_TESTS=1 by the repo
conftest. Identifiers are confirmed live in-run (the arXiv abstract is fetched
and its real numbers asserted), never hardcoded from an unverified memory.

Constitution Principle III: real calls, no mocks.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.grounding_guard import (
    CitedClaim,
    ground_claim,
    verify_grounding_and_clean,
)
from llmxive.types import CitationKind

# A real, resolvable arXiv id whose abstract we confirm in-run.
_REAL_ARXIV = "1706.03762"  # "Attention Is All You Need"


def _real_abstract_numbers() -> tuple[str, str]:
    """Fetch the real abstract live and return (a number IN it, a number NOT in it).

    Confirms the grounded/ungrounded fixtures against the LIVE source rather than
    a hardcoded assumption.
    """
    from llmxive.librarian.verify import _fetch_from_arxiv

    title, abstract = _fetch_from_arxiv(_REAL_ARXIV)
    blob = " ".join(filter(None, [title, abstract]))
    assert "28.4" in blob, f"expected '28.4' (BLEU) in live abstract; got {blob[:200]!r}"
    assert "9988" not in blob and "9,988" not in blob
    return "28.4", "9988"


def test_freetext_only_citation_is_flagged() -> None:
    """The trail's exact case: a number on a free-text author-year citation."""
    claim = CitedClaim(
        claim_text="There are 1,296 prime knots with 13 crossings "
        "(Kauffman & Lambropoulou 2004).",
        number="1296",
        source_str="Kauffman & Lambropoulou 2004",  # no resolvable id
    )
    verdict = ground_claim(claim)
    assert verdict.ok is False
    assert "free-text" in verdict.reason


def test_number_not_in_cited_source_is_flagged() -> None:
    """A number cited to a REAL arXiv paper whose abstract lacks it → flagged."""
    _, absent = _real_abstract_numbers()
    claim = CitedClaim(
        claim_text=f"There are {absent} prime knots with 13 crossings (arXiv:{_REAL_ARXIV}).",
        number=absent,
        source_str=f"arXiv:{_REAL_ARXIV}",
        source_kind=CitationKind.ARXIV,
        source_value=_REAL_ARXIV,
    )
    verdict = ground_claim(claim)
    assert verdict.ok is False
    assert "does not substantiate" in verdict.reason


def test_grounded_number_is_not_flagged() -> None:
    """A number that DOES appear in the cited source's abstract → NOT flagged."""
    present, _ = _real_abstract_numbers()
    claim = CitedClaim(
        claim_text=f"The model achieves {present} BLEU (arXiv:{_REAL_ARXIV}).",
        number=present,
        source_str=f"arXiv:{_REAL_ARXIV}",
        source_kind=CitationKind.ARXIV,
        source_value=_REAL_ARXIV,
    )
    verdict = ground_claim(claim)
    assert verdict.ok is True, verdict.reason


def test_fabricated_arxiv_source_unreachable_is_flagged() -> None:
    """A malformed/unreachable arXiv id used as a source → flagged (unreachable)."""
    claim = CitedClaim(
        claim_text="There are 9,988 prime knots (Lee et al. 2024, arXiv:2402.13).",
        number="9988",
        source_str="Lee et al. 2024, arXiv:2402.13",
        source_kind=CitationKind.ARXIV,
        source_value="2402.13",
    )
    verdict = ground_claim(claim)
    assert verdict.ok is False
    assert "unreachable" in verdict.reason


def test_orchestrator_extracts_and_flags_freetext_claim() -> None:
    """Full pass: real LLM extraction → free-text claim flagged ``[UNVERIFIED]``.

    Exercises ``verify_grounding_and_clean`` end-to-end with a REAL backend so
    the extraction LLM call runs. The doc mixes a fabricated number on a
    free-text citation (must be flagged) with an uncited design threshold (must
    be left untouched — the scope guard).
    """
    from llmxive.backends.dartmouth import DartmouthBackend

    backend = DartmouthBackend()
    doc = (
        "# Knot complexity\n\n"
        "There are 1,296 prime knots with 13 crossings "
        "(Kauffman & Lambropoulou 2004).\n\n"
        "The success threshold is R-squared >= 0.05 (a design choice).\n"
    )
    cleaned, report = verify_grounding_and_clean(
        doc, backend=backend, model=None, repo_root=Path(__file__).resolve().parents[2]
    )
    # The fabricated free-text-cited claim is flagged.
    assert "[UNVERIFIED:" in cleaned, cleaned
    assert report.flagged_count >= 1
    # The uncited design threshold is NEVER touched (precision guard).
    assert "R-squared >= 0.05" in cleaned
