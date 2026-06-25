"""Spec 020 — deterministic empirical-value strip + the planning GUARANTEE (offline).

``planning_scan.strip_empirical_values`` removes high-confidence empirical values
(comma-grouped counts, percentages, timed quantities) while preserving structural
numbers. The integration test proves the GUARANTEE: even when the LLM extractor
returns ZERO claims (its non-deterministic worst case), the planning branch still
strips the empirical value via this deterministic pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llmxive.claims import service as svc
from llmxive.claims.gate import CLAIM_MARKER_PREFIX
from llmxive.claims.planning_scan import has_empirical_value, strip_empirical_values


@pytest.mark.parametrize(
    "text,gone",
    [
        ("There are 27,635 prime knots.", "27,635"),
        ("~2,000 prime knots downloaded.", "2,000"),
        ("approximately 95% of records are clean.", "95%"),
        ("The first 1,701,936 knots.", "1,701,936"),
        ("Ingest takes approximately 15 minutes.", "15 minutes"),
    ],
)
def test_strips_empirical(text: str, gone: str) -> None:
    out = strip_empirical_values(text)
    assert gone not in out
    assert not has_empirical_value(out)


@pytest.mark.parametrize(
    "text,kept",
    [
        ("prime knots at ≤13 crossings", "13"),       # scope bound
        ("crossing number 13", "13"),                  # index
        ("crossing numbers 1-10", "1-10"),             # range
        ("Phase 1 analysis", "Phase 1"),               # phase
        ("checksummed via SHA-256", "SHA-256"),        # identifier
        ("version 1.0.0 ratified", "1.0.0"),           # version
        ("on 2026-05-29", "2026-05-29"),               # date
        ("citation title overlap ≥0.7", "0.7"),        # bare decimal threshold
        ("dataset ds002800", "ds002800"),              # dataset id
        # Spec 023 defect #16: bound-led values are CHOSEN DESIGN TARGETS
        # (requirements the project sets), not empirical claims — stripping
        # them made every success criterion untestable and put the
        # testability reviewers at war with the strip (observed live on
        # PROJ-552's spec panel: the reviser restored "≥80%", the strip
        # deleted it, the reviewer re-flagged the hole, forever).
        ("≥95% data completeness.", "95%"),            # target
        ("reference coverage ≥10%.", "10%"),           # target
        ("Complete within 15 minutes.", "15 minutes"),  # time budget
        ("at least 80% statistical power", "80%"),     # target
        ("minimum 80% power", "80%"),                  # target
        # Spec 023 #16b: bare timed values are design parameters
        # (timeouts/backoffs/budgets), never world-claims.
        ("Exponential backoff (1s → 60s max).", "60s"),
        ("per-pass timeout 30 ms", "30 ms"),
    ],
)
def test_preserves_structural(text: str, kept: str) -> None:
    assert kept in strip_empirical_values(text)


def test_idempotent_and_headers_and_fences() -> None:
    doc = (
        "# Heading with 27,635 in it\n"
        "There are 27,635 knots, ≥95% complete.\n"
        "```\ncode with 1,234 stays\n```\n"
    )
    once = strip_empirical_values(doc)
    # header line + fenced code are untouched
    assert "# Heading with 27,635 in it" in once
    assert "code with 1,234 stays" in once
    # the prose claim value is deferred; the bound-led target survives (#16)
    assert "27,635 knots" not in once.split("\n")[1]
    assert "≥95% complete" in once
    assert strip_empirical_values(once) == once  # idempotent


def _lowlevel_claim_doc() -> str:
    return (
        "# Plan\n\n## Scale/Scope\n\n"
        "~2,000 prime knots (1-10), ~27,635 at crossing number 13 (Phase 1).\n"
    )


def test_planning_branch_guarantees_strip_even_when_extractor_finds_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Simulate the LLM extractor's worst case: it returns ZERO claims. The
    # deterministic pass must STILL strip the empirical values (the guarantee).
    monkeypatch.setattr(svc, "extract_claims", lambda *a, **k: [])

    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("resolve() called in a planning stage")

    monkeypatch.setattr(svc, "resolve", _boom)

    out, claims, report = svc.process_document(
        _lowlevel_claim_doc(),
        artifact_path="projects/PROJ-x/specs/plan.md",
        project_id="PROJ-x", backend=object(), model=None,
        repo_root=tmp_path, stage_label="plan",
    )
    assert "27,635" not in out and "2,000" not in out      # stripped (guaranteed)
    assert "crossing number 13" in out and "Phase 1" in out  # structural preserved
    assert CLAIM_MARKER_PREFIX not in out                   # still no kickback
    assert report.blocked is False
    assert claims == []


def test_is_design_target_predicate() -> None:
    """Spec 023 defect #23: bound-led design targets are NOT empirical
    world-claims and must be protected from the LLM smooth path."""
    from llmxive.claims.planning_scan import is_design_target

    # The exact PROJ-552 spans the smooth layer was paraphrasing to vague:
    assert is_design_target(
        "≥ 95% of knots with computable invariants have all invariants populated")
    assert is_design_target("achieves ≥ 90% match against reference values")
    assert is_design_target("residuals exceeding ≥ 2 standard deviations")
    assert is_design_target("at least 80% statistical power")
    assert is_design_target("within 60 minutes")
    assert is_design_target("up to 13 crossings")
    # Genuine empirical world-claims remain smoothable:
    assert not is_design_target("a dataset of 9,988 prime knots")
    assert not is_design_target("approximately 27,635 papers")
    assert not is_design_target("the overwhelming majority of knots")


def test_planning_smooth_preserves_design_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The LLM claim path must NOT smooth a bound-led design target into a
    vague qualifier (the PROJ-552 spec non-convergence root: ≥95% kept being
    paraphrased to 'the vast majority', re-flagged every round)."""
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus

    target = "≥ 95% of knots with computable invariants have all invariants populated"
    doc = f"# Spec\n\n## Success Criteria\n\n- **SC-005**: {target}.\n"

    claim = Claim(
        claim_id="c_test001", kind=ClaimKind.MAGNITUDE, raw_text=target,
        canonical=target, context="SC-005", artifact_path="x/spec.md",
        source_type="pending", status=ClaimStatus.PENDING, resolved_value=None,
        evidence=None, resolver=None, attempts=0, updated_at="2026-06-14T00:00:00Z",
    )
    monkeypatch.setattr(svc, "extract_claims", lambda *a, **k: [claim])

    def _must_not_smooth(*a: Any, **k: Any) -> Any:
        raise AssertionError("strip_and_smooth() called on a design target")

    monkeypatch.setattr(svc, "strip_and_smooth", _must_not_smooth)

    out, _claims, report = svc.process_document(
        doc, artifact_path="projects/PROJ-x/specs/spec.md",
        project_id="PROJ-x", backend=object(), model=None,
        repo_root=tmp_path, stage_label="spec",
    )
    # The concrete ≥ 95% survives verbatim; no vague paraphrase introduced.
    assert "≥ 95%" in out
    assert report.blocked is False


def test_confidence_level_is_a_design_parameter_not_deferred() -> None:
    """A confidence level / CI width is a statistical DESIGN parameter (like a
    bound-led target or alpha), NOT an empirical claim. Deferring it yields
    "[deferred] confidence level", which the testability/soundness panels re-flag
    as unverifiable forever (the PROJ-492 spec non-convergence loop). Keep it."""
    from llmxive.claims.planning_scan import strip_empirical_values

    for text, val in [
        ("evaluated at a 95% confidence level", "95%"),
        ("a Wilson 95% CI for the proportion", "95%"),
        ("the confidence level of 99% must hold", "99%"),
        ("report a 90% credible interval", "90%"),
    ]:
        assert val in strip_empirical_values(text), text
    # A genuine empirical value with NO statistical-design context is still deferred.
    assert "27,635" not in strip_empirical_values("approximately 27,635 papers were found")
    assert "[deferred]" in strip_empirical_values("the inconsistency rate was 30% overall")


def test_tolerance_threshold_margin_are_design_parameters_not_deferred() -> None:
    """A tolerance / threshold / margin is the operator-CHOSEN cutoff a rule
    compares against — a design parameter, exactly like a confidence level. The
    live FR-004 loop on PROJ-492: the reviser sets a concrete "relative tolerance
    of 0.05", the strip re-defers it to "[deferred] relative tolerance", the
    testability/soundness panels re-flag it forever. Keep these concrete."""
    from llmxive.claims.planning_scan import strip_empirical_values

    for text, val in [
        ("flag inconsistent when the relative tolerance of 0.05 is exceeded", "0.05"),
        ("a discrepancy threshold of 0.1 between reported and reconstructed p", "0.1"),
        ("agree to within a margin of 0.02", "0.02"),
    ]:
        assert val in strip_empirical_values(text), text
    # Still deferred: an OBSERVED quantity with no design-parameter context.
    assert "[deferred]" in strip_empirical_values("the dataset contained 1,234 experiments")
