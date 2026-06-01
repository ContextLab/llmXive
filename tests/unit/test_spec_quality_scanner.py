"""Unit tests for the deterministic spec-quality scanner (spec 015 hardening).

The scanner backstops the LLM panel lenses, which reliably MISS mechanical
regressions that slipped into PROJ-552's "converged" spec: surviving
``[NEEDS CLARIFICATION: …]`` markers, a ``[DATE]`` template placeholder, and a
duplicate functional requirement (FR-008 ≈ FR-010). These tests use the exact
PROJ-552 defect shapes (real inputs) and verify a CLEAN spec yields zero
findings (no false positives).
"""

from __future__ import annotations

from llmxive.speckit._spec_quality import SpecQualityFinding, scan_spec_quality

# A minimal but realistic CLEAN spec: no markers, distinct FRs, no placeholders.
_CLEAN_SPEC = """\
# Feature Specification: Knot-diagram complexity

**Feature Branch**: `552-quantifying-the-complexity-of-knot-diagr`
**Created**: 2026-05-29
**Status**: Clarified

## Requirements

- **FR-001**: The system MUST compute the crossing number for each diagram.
- **FR-002**: The system MUST compute the braid index for each diagram.
- **FR-003**: The system MUST report the Spearman correlation with arc index.

## Success Criteria

- **SC-001**: Correlations are reported with 95% confidence intervals.
"""


def test_clean_spec_yields_zero_findings():
    """A clean spec (no placeholders, distinct FRs, no NEEDS-CLARIFICATION)
    must produce NO findings — the scanner must not false-positive."""
    assert scan_spec_quality(_CLEAN_SPEC) == []


def test_empty_text_yields_zero_findings():
    assert scan_spec_quality("") == []


def test_needs_clarification_marker_flagged():
    """The exact PROJ-552 defect: surviving [NEEDS CLARIFICATION: …] markers."""
    spec = _CLEAN_SPEC + (
        "\n- **FR-004**: The metric MUST validate against "
        "[NEEDS CLARIFICATION: which independent invariant?].\n"
        "- **FR-005**: Report results [NEEDS CLARIFICATION: at what scale?].\n"
    )
    findings = scan_spec_quality(spec)
    nc = [f for f in findings if f.kind == "needs_clarification"]
    assert len(nc) == 2
    assert all(isinstance(f, SpecQualityFinding) for f in nc)
    assert "NEEDS CLARIFICATION" in nc[0].text


def test_date_template_placeholder_flagged():
    """The exact PROJ-552 defect: an unfilled [DATE] placeholder."""
    spec = _CLEAN_SPEC.replace("**Created**: 2026-05-29", "**Created**: [DATE]")
    findings = scan_spec_quality(spec)
    ph = [f for f in findings if f.kind == "template_placeholder"]
    assert len(ph) == 1
    assert ph[0].text == "[DATE]"


def test_link_and_branchname_placeholders_flagged():
    spec = _CLEAN_SPEC + (
        "\nSee the design doc at [link].\n"
        "**Feature Branch**: `[NNN-feature-name]`\n"
    )
    findings = scan_spec_quality(spec)
    kinds = [f.text for f in findings if f.kind == "template_placeholder"]
    assert "[link]" in kinds
    assert "[NNN-feature-name]" in kinds


def test_leftover_speckit_instruction_line_flagged():
    spec = _CLEAN_SPEC + (
        "\n**Input**: *(filled in by the `/speckit-specify` command)*\n"
    )
    findings = scan_spec_quality(spec)
    instr = [f for f in findings if "scaffolding instruction" in f.reason]
    assert len(instr) == 1
    assert "/speckit-specify" in instr[0].text


def test_duplicate_requirement_flagged():
    """The exact PROJ-552 defect shape: FR-008 ≈ FR-010 (near-identical text)."""
    spec = _CLEAN_SPEC + (
        "\n- **FR-008**: The system MUST validate the composite metric against "
        "the arc index using Spearman correlation.\n"
        "- **FR-009**: The system MUST output a CSV summary table.\n"
        "- **FR-010**: The system MUST validate the composite metric against the "
        "arc-index, using Spearman correlation.\n"
    )
    findings = scan_spec_quality(spec)
    dups = [f for f in findings if f.kind == "duplicate_requirement"]
    assert len(dups) == 1
    assert "FR-008" in dups[0].text and "FR-010" in dups[0].text


def test_distinct_requirements_not_flagged_as_duplicate():
    """Two genuinely different FRs (sharing some words) must NOT be flagged."""
    spec = _CLEAN_SPEC + (
        "\n- **FR-008**: The system MUST compute the Seifert circle count.\n"
        "- **FR-010**: The system MUST compute the genus of the knot.\n"
    )
    dups = [f for f in scan_spec_quality(spec) if f.kind == "duplicate_requirement"]
    assert dups == []


def test_normalization_ignores_case_punctuation_and_spacing():
    """Duplicate detection normalizes whitespace/punctuation/case."""
    spec = (
        "- **FR-001**: The system MUST log every run.\n"
        "- **FR-002**: the   System must LOG every run!!!\n"
    )
    dups = [f for f in scan_spec_quality(spec) if f.kind == "duplicate_requirement"]
    assert len(dups) == 1


def test_scanner_flags_paraphrase_duplicate_fr_not_just_exact():
    """Regression: the REAL PROJ-552 duplicate (FR-008 vs FR-010) differs by a
    couple of filler words ('including'/'and'), so exact-normalized equality
    missed it. Token-set (Jaccard) similarity must catch the paraphrase."""
    from llmxive.speckit._spec_quality import scan_spec_quality

    spec = (
        "### Functional Requirements\n"
        "- **FR-008**: System MUST apply statistical tests (Pearson/Spearman "
        "correlation, ANOVA for group differences) to assess significance of findings\n"
        "- **FR-010**: System MUST apply statistical tests including Pearson/Spearman "
        "correlation and ANOVA for group differences to assess significance of findings\n"
    )
    dups = [f for f in scan_spec_quality(spec) if f.kind == "duplicate_requirement"]
    assert len(dups) == 1, dups
    assert "FR-008" in dups[0].text and "FR-010" in dups[0].text


def test_scanner_no_false_duplicate_on_distinct_frs_sharing_boilerplate():
    """Distinct FRs that share only 'System MUST …' boilerplate must NOT be
    flagged as duplicates (no false positives)."""
    from llmxive.speckit._spec_quality import scan_spec_quality

    spec = (
        "### Functional Requirements\n"
        "- **FR-001**: System MUST download knot data from Knot Atlas for all knots with crossing number 13\n"
        "- **FR-002**: System MUST parse and clean the dataset to extract consistent invariant representations\n"
        "- **FR-003**: System MUST compute arc index and bridge number from diagram representations\n"
    )
    assert [f for f in scan_spec_quality(spec) if f.kind == "duplicate_requirement"] == []
