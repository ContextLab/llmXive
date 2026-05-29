"""Tests for the runner-version filter on
``llmxive.calibration.sensitivity.recommend_sensitivity``.

FR-044 noise robustness says calibration MUST be run repeatedly for
the same code state. After a calibration runner / panel-prompt
adjustment, the OLD reports are stale and must NOT be aggregated with
the post-adjustment reports — but the SAME reports can be aggregated
within either cohort. The runner-version tag (typically a git short
hash) enables this filtering.
"""

from __future__ import annotations

import pytest

from llmxive.calibration.differential import AdjudicationReport, CalibrationRun
from llmxive.calibration.injectors import Injection
from llmxive.calibration.sensitivity import (
    SensitivityDirection,
    recommend_sensitivity,
)
from llmxive.convergence.types import (
    Concern,
    ConvergenceResult,
    Severity,
    Verdict,
)


def _make_run(*, expected_lens: str, caught: bool) -> CalibrationRun:
    concerns = []
    verdicts = []
    if caught:
        c = Concern(
            id="C001", reviewer=expected_lens, severity=Severity.SCIENCE,
            artifact="x", location="", text="",
        )
        concerns.append(c)
        verdicts.append(Verdict(concern_id=c.id, reviewer=expected_lens, status="fail"))
    injected = ConvergenceResult(
        stage="clarified", converged=not caught, rounds_used=1,
        concern_history=concerns, verdict_history=verdicts,
    )
    clean = ConvergenceResult(
        stage="clarified", converged=True, rounds_used=1,
    )
    return CalibrationRun(
        injector_name="x", injection=Injection(
            text="", expected_lens=expected_lens, description="",
            original="clarified",
        ),
        clean_result=clean, injected_result=injected,
    )


# --- Version filter ---------------------------------------------------


def test_version_filter_excludes_non_matching_reports():
    """Stale reports (different version) are EXCLUDED from aggregation."""
    pre_fix = AdjudicationReport(runs=[
        _make_run(expected_lens="methodology", caught=False),
    ])
    post_fix = AdjudicationReport(runs=[
        _make_run(expected_lens="methodology", caught=True),
    ])
    # Aggregate ONLY the post-fix report.
    recs = recommend_sensitivity(
        [pre_fix, post_fix],
        version_filter="abc1234",
        report_versions=["old-version", "abc1234"],
    )
    assert recs[0].lens == "methodology"
    # Only the post-fix run was counted → it CAUGHT → STABLE.
    assert recs[0].direction is SensitivityDirection.STABLE
    assert recs[0].runs_observed == 1
    assert recs[0].caught_count == 1
    assert recs[0].missed_count == 0


def test_version_filter_excludes_untagged_reports():
    """A report with runner_version=None (legacy / unknown) is
    EXCLUDED when a version_filter is active (fail closed)."""
    untagged = AdjudicationReport(runs=[
        _make_run(expected_lens="methodology", caught=False),
    ])
    tagged = AdjudicationReport(runs=[
        _make_run(expected_lens="methodology", caught=True),
    ])
    recs = recommend_sensitivity(
        [untagged, tagged],
        version_filter="abc1234",
        report_versions=[None, "abc1234"],
    )
    assert recs[0].runs_observed == 1
    assert recs[0].caught_count == 1


def test_version_filter_accepts_set_of_versions():
    """Multiple acceptable versions for cross-iteration aggregation."""
    r1 = AdjudicationReport(runs=[_make_run(expected_lens="methodology", caught=True)])
    r2 = AdjudicationReport(runs=[_make_run(expected_lens="methodology", caught=True)])
    r3 = AdjudicationReport(runs=[_make_run(expected_lens="methodology", caught=False)])
    recs = recommend_sensitivity(
        [r1, r2, r3],
        version_filter={"v1", "v2"},
        report_versions=["v1", "v2", "old-pre-fix"],
    )
    assert recs[0].runs_observed == 2
    assert recs[0].caught_count == 2
    # Old missed run was excluded → STABLE.
    assert recs[0].direction is SensitivityDirection.STABLE


def test_no_version_filter_aggregates_everything():
    """When version_filter is None, every report counts (back-compat)."""
    r1 = AdjudicationReport(runs=[_make_run(expected_lens="methodology", caught=True)])
    r2 = AdjudicationReport(runs=[_make_run(expected_lens="methodology", caught=False)])
    recs = recommend_sensitivity(
        [r1, r2],
        report_versions=["v1", "v2"],
    )
    assert recs[0].runs_observed == 2
    # Missing one → INCREASE (recall floor violated; FR-044 priority).
    assert recs[0].direction is SensitivityDirection.INCREASE


def test_version_filter_without_versions_raises():
    r = AdjudicationReport(runs=[_make_run(expected_lens="x", caught=True)])
    with pytest.raises(ValueError, match="requires report_versions"):
        recommend_sensitivity([r], version_filter="abc")


def test_versions_wrong_length_raises():
    r = AdjudicationReport(runs=[_make_run(expected_lens="x", caught=True)])
    with pytest.raises(ValueError, match="length"):
        recommend_sensitivity(
            [r], version_filter="abc",
            report_versions=["a", "b"],  # too long
        )


def test_filter_to_only_old_version_excludes_all_recent():
    """If the filter matches NO included reports, the recommender
    returns no recommendations (degenerate case)."""
    r1 = AdjudicationReport(runs=[_make_run(expected_lens="m", caught=True)])
    r2 = AdjudicationReport(runs=[_make_run(expected_lens="m", caught=True)])
    recs = recommend_sensitivity(
        [r1, r2],
        version_filter="old-version",
        report_versions=["v1", "v2"],
    )
    assert recs == []


# --- Adjudication keys still resolve correctly under filtering --------


def test_adjudication_keys_preserve_original_report_indices():
    """When a filter excludes a report, the adjudication dict's
    (report_index, ...) keys MUST still resolve via the ORIGINAL
    indexing (not a renumbering of the surviving reports).
    """
    # Build two reports each with one extra-finding on clean.
    def _with_extra(caught: bool) -> AdjudicationReport:
        concerns = [Concern(
            id="X001", reviewer="methodology", severity=Severity.WRITING,
            artifact="x", location="", text="extra clean finding",
        )]
        verdicts = [Verdict(concern_id="X001", reviewer="methodology", status="fail")]
        clean = ConvergenceResult(
            stage="clarified", converged=True, rounds_used=1,
            concern_history=concerns, verdict_history=verdicts,
        )
        injected_concerns = []
        injected_verdicts = []
        if caught:
            ic = Concern(
                id="I001", reviewer="methodology", severity=Severity.SCIENCE,
                artifact="x", location="", text="",
            )
            injected_concerns.append(ic)
            injected_verdicts.append(
                Verdict(concern_id="I001", reviewer="methodology", status="fail")
            )
        injected = ConvergenceResult(
            stage="clarified", converged=not caught, rounds_used=1,
            concern_history=injected_concerns,
            verdict_history=injected_verdicts,
        )
        return AdjudicationReport(runs=[CalibrationRun(
            injector_name="x", injection=Injection(
                text="", expected_lens="methodology", description="",
                original="clarified",
            ),
            clean_result=clean, injected_result=injected,
        )])

    r_old = _with_extra(caught=False)
    r_new = _with_extra(caught=True)
    # Adjudication keys USE the original report-index (0 = old, 1 = new).
    # We mark the OLD extra as 'spurious' and the NEW as 'spurious' too.
    adj = {
        (0, 0, 0): "spurious",  # ← excluded by filter
        (1, 0, 0): "spurious",  # ← included
    }
    recs = recommend_sensitivity(
        [r_old, r_new], adjudication=adj,
        version_filter="v_new", report_versions=["v_old", "v_new"],
    )
    # Only the v_new spurious count was used; the v_old key never
    # touched the tally even though it was in the dict.
    assert recs[0].spurious_extras_count == 1
