"""Unit tests (OFFLINE — no network) for the F-18 citation strip/flag guard.

The guard ensures pipeline stages never publish fabricated / unresolvable
references (Constitution Principle II). These tests exercise:

1. Hardened extraction in ``reference_validator.extract_citations``: a
   MALFORMED arXiv ref (``arXiv:2402.13`` — real ids are ``\\d{4}.\\d{4,5}``)
   must be captured as an arxiv-kind citation so it can be flagged. The old
   regex silently dropped it, which let the fabricated PROJ-552 reference slip
   past the panel.
2. The PURE ``apply_citation_verdicts`` rewriter: given REAL doc text plus a
   set of verdicts, it marks exactly the FAILED references ``[UNVERIFIED: ...]``
   in-place (keeping the human-readable claim/title), leaves VERIFIED refs
   byte-for-byte untouched, and preserves the surrounding prose.

No mocks: the verdicts are real data structures; the rewrite is pure string
work; nothing here touches the network.
"""

from __future__ import annotations

from llmxive.agents.citation_guard import (
    CitationVerdict,
    GuardReport,
    apply_citation_verdicts,
)
from llmxive.agents.reference_validator import extract_citations
from llmxive.types import CitationKind

# --- 1. hardened extraction -------------------------------------------------


def test_extract_captures_malformed_arxiv() -> None:
    text = (
        "The minimal crossing diagram count is 9,988 "
        "(Lee et al. 2024, arXiv:2402.13)."
    )
    cits = extract_citations(text)
    arxiv = [c for c in cits if c.kind == CitationKind.ARXIV]
    assert any(c.value == "2402.13" for c in arxiv), (
        f"malformed arXiv:2402.13 must be extracted; got {[c.value for c in arxiv]}"
    )


def test_extract_still_captures_well_formed_arxiv() -> None:
    text = "Attention is all you need (arXiv:1706.03762)."
    cits = extract_citations(text)
    arxiv = [c for c in cits if c.kind == CitationKind.ARXIV]
    assert [c.value for c in arxiv] == ["1706.03762"]


def test_extract_malformed_and_wellformed_together() -> None:
    text = "See arXiv:1706.03762 and the fabricated arXiv:2402.13 ref."
    values = {c.value for c in extract_citations(text) if c.kind == CitationKind.ARXIV}
    assert "1706.03762" in values
    assert "2402.13" in values


# --- 2. pure verdict rewriter ----------------------------------------------


def test_apply_verdicts_marks_failed_leaves_verified() -> None:
    text = (
        "The count is 9,988 (Lee et al. 2024, arXiv:2402.13). "
        "A dead link is [Dataset](https://nope.example/404). "
        "A good ref is arXiv:1706.03762."
    )
    verdicts = [
        CitationVerdict(value="2402.13", kind=CitationKind.ARXIV, ok=False,
                        reason="malformed arXiv id (not \\d{4}.\\d{4,5})"),
        CitationVerdict(value="https://nope.example/404", kind=CitationKind.URL,
                        ok=False, reason="404 Not Found"),
        CitationVerdict(value="1706.03762", kind=CitationKind.ARXIV, ok=True,
                        reason=""),
    ]
    cleaned, report = apply_citation_verdicts(text, verdicts)

    # Failed bare-arxiv ref → marked, original ref preserved inside the marker.
    assert "[UNVERIFIED: arXiv:2402.13" in cleaned
    assert "malformed arXiv id" in cleaned
    # Failed markdown link → title kept, marker appended, raw 404 target gone.
    assert "Dataset" in cleaned
    assert "[UNVERIFIED:" in cleaned
    assert "(https://nope.example/404)" not in cleaned
    # Verified ref → byte-for-byte untouched.
    assert "arXiv:1706.03762" in cleaned
    assert cleaned.count("[UNVERIFIED:") == 2
    # Surrounding prose preserved.
    assert "The count is 9,988" in cleaned
    assert isinstance(report, GuardReport)
    assert report.flagged_count == 2
    assert report.verified_count == 1
    assert "2402.13" in report.flagged_values


def test_apply_verdicts_noop_when_all_verified() -> None:
    text = "Good ref arXiv:1706.03762 and [Paper](https://arxiv.org/abs/1706.03762)."
    verdicts = [
        CitationVerdict(value="1706.03762", kind=CitationKind.ARXIV, ok=True, reason=""),
        CitationVerdict(value="https://arxiv.org/abs/1706.03762",
                        kind=CitationKind.URL, ok=True, reason=""),
    ]
    cleaned, report = apply_citation_verdicts(text, verdicts)
    assert cleaned == text  # untouched
    assert report.flagged_count == 0
    assert report.verified_count == 2


def test_apply_verdicts_idempotent_on_already_marked() -> None:
    """Re-running the guard on already-marked text must not double-wrap."""
    text = "Count 9,988 (Lee et al. 2024, arXiv:2402.13)."
    verdict = CitationVerdict(value="2402.13", kind=CitationKind.ARXIV, ok=False,
                              reason="malformed")
    once, _ = apply_citation_verdicts(text, [verdict])
    twice, report2 = apply_citation_verdicts(once, [verdict])
    assert once == twice
    assert once.count("[UNVERIFIED:") == 1
    assert report2.flagged_count == 0  # nothing left to flag the second time


def test_apply_verdicts_preserves_doi_claim_text() -> None:
    text = "As shown (doi:10.1234/fake.9999) the result holds."
    verdict = CitationVerdict(value="10.1234/fake.9999", kind=CitationKind.DOI,
                              ok=False, reason="DOI not found")
    cleaned, report = apply_citation_verdicts(text, [verdict])
    assert "[UNVERIFIED: 10.1234/fake.9999" in cleaned
    assert "the result holds" in cleaned
    assert report.flagged_count == 1
