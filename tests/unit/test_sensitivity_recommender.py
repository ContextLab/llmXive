"""Unit tests for the FR-044 adaptive sensitivity recommender.

The recommender consumes :class:`AdjudicationReport`s + the maintainer's
extra-findings adjudication and produces per-lens recommendations:

* INCREASE — any missed injected flaw on the lens
* REDUCE   — many spurious extras adjudicated on clean artifacts
* STABLE   — within tolerance

These tests cover the threshold semantics, the noise-robustness
behavior across multiple reports (multiple seeds = higher confidence),
and the rendering output. NO mocks — every test builds real
CalibrationRun objects.
"""

from __future__ import annotations

from llmxive.calibration.differential import AdjudicationReport, CalibrationRun
from llmxive.calibration.injectors import Injection
from llmxive.calibration.sensitivity import (
    SensitivityDirection,
    recommend_sensitivity,
    render_recommendations_markdown,
)
from llmxive.convergence.types import (
    Concern,
    ConvergenceResult,
    Severity,
    Verdict,
)


def _make_result(
    *, stage: str, lens_concerns: list[tuple[str, str]], converged: bool,
) -> ConvergenceResult:
    """Build a ConvergenceResult with the given (lens, concern_text) pairs
    as concern_history. Each pair becomes one Concern attributed to the
    named lens; the verdict_history pairs each Concern with a 'fail'
    Verdict from the same lens so the differential's `_summarize`
    correctly classes the lens as flagged."""
    concerns: list[Concern] = []
    verdicts: list[Verdict] = []
    for i, (lens, text) in enumerate(lens_concerns):
        c = Concern(
            id=f"C{i + 1:03d}", reviewer=lens, severity=Severity.SCIENCE,
            artifact="a.md", location="", text=text,
        )
        concerns.append(c)
        verdicts.append(
            Verdict(concern_id=c.id, reviewer=lens, status="fail")
        )
    return ConvergenceResult(
        stage=stage, converged=converged, rounds_used=1,
        concern_history=concerns, verdict_history=verdicts,
    )


def _make_run(
    *, injector_name: str, expected_lens: str, clean_concerns: list[tuple[str, str]],
    injected_concerns: list[tuple[str, str]],
) -> CalibrationRun:
    clean = _make_result(stage="clarified", lens_concerns=clean_concerns, converged=True)
    injected = _make_result(stage="clarified", lens_concerns=injected_concerns, converged=False)
    return CalibrationRun(
        injector_name=injector_name,
        injection=Injection(
            text="x", expected_lens=expected_lens,
            description=f"{injector_name} injection", original="clarified",
        ),
        clean_result=clean,
        injected_result=injected,
    )


# ---------- INCREASE: missed injected flaw ------------------------------


def test_missed_injected_flaw_triggers_increase():
    """FR-044: a single missed injection on a lens → INCREASE that lens."""
    # Injected on `methodology` but injected_result has NO methodology
    # concerns → the flaw was missed.
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[],
        injected_concerns=[("requirements_coverage", "unrelated")],
    )
    report = AdjudicationReport(runs=[run])
    recs = recommend_sensitivity([report])
    assert len(recs) == 1
    assert recs[0].lens == "methodology"
    assert recs[0].direction is SensitivityDirection.INCREASE
    assert recs[0].missed_count == 1


def test_caught_flaw_no_extras_is_stable():
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[],
        injected_concerns=[("methodology", "found the flaw")],
    )
    recs = recommend_sensitivity([AdjudicationReport(runs=[run])])
    assert recs[0].direction is SensitivityDirection.STABLE
    assert recs[0].caught_count == 1


# ---------- REDUCE: many spurious extras --------------------------------


def test_three_spurious_extras_triggers_reduce():
    """FR-044: 3 spurious extras on a lens → REDUCE that lens.

    The threshold default is 3; only adjudicated-spurious extras count.
    """
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        # Clean has 3 extras all on the `requirements_coverage` lens.
        clean_concerns=[
            ("requirements_coverage", "nit 1"),
            ("requirements_coverage", "nit 2"),
            ("requirements_coverage", "nit 3"),
        ],
        injected_concerns=[("methodology", "found the flaw")],
    )
    report = AdjudicationReport(runs=[run])
    # Maintainer marks all 3 extras as spurious for the methodology
    # report (the report is indexed at (report_index=0, run_index=0,
    # finding_index=0..2)).
    adjudication = {
        (0, 0, 0): "spurious",
        (0, 0, 1): "spurious",
        (0, 0, 2): "spurious",
    }
    recs = recommend_sensitivity(
        [report], adjudication=adjudication,
    )
    # The recommendation is keyed by EXPECTED lens (methodology), not
    # by the lens that produced the extras (per the design — the
    # injected case's expected lens identifies the calibration unit
    # under test).
    rec = next(r for r in recs if r.lens == "methodology")
    assert rec.direction is SensitivityDirection.REDUCE
    assert rec.spurious_extras_count == 3


def test_two_spurious_extras_is_below_default_threshold_so_stable():
    """Per the design doc: 'minor FPs that resolve within one
    review/revision round are acceptable'. Default threshold = 3."""
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[
            ("methodology", "nit 1"), ("methodology", "nit 2"),
        ],
        injected_concerns=[("methodology", "found the flaw")],
    )
    adjudication = {(0, 0, 0): "spurious", (0, 0, 1): "spurious"}
    recs = recommend_sensitivity(
        [AdjudicationReport(runs=[run])], adjudication=adjudication,
    )
    assert recs[0].direction is SensitivityDirection.STABLE


def test_legitimate_extras_do_not_trigger_reduce():
    """Adjudicated-legitimate extras mean the panel correctly noticed a
    flaw in the supposedly-clean sample → fix the sample, NOT the
    prompt. Sensitivity stays STABLE."""
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[
            ("methodology", "real issue 1"),
            ("methodology", "real issue 2"),
            ("methodology", "real issue 3"),
            ("methodology", "real issue 4"),
        ],
        injected_concerns=[("methodology", "found the flaw")],
    )
    adjudication = {
        (0, 0, 0): "legitimate", (0, 0, 1): "legitimate",
        (0, 0, 2): "legitimate", (0, 0, 3): "legitimate",
    }
    recs = recommend_sensitivity(
        [AdjudicationReport(runs=[run])], adjudication=adjudication,
    )
    assert recs[0].direction is SensitivityDirection.STABLE
    assert recs[0].legitimate_extras_count == 4
    assert recs[0].spurious_extras_count == 0


# ---------- INCREASE wins over REDUCE -----------------------------------


def test_missed_flaw_wins_over_spurious_extras():
    """FR-044 ordering: a missed injection is the recall floor — fix
    that FIRST even if the lens also over-flags."""
    run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[("methodology", "nit 1"), ("methodology", "nit 2"),
                        ("methodology", "nit 3"), ("methodology", "nit 4")],
        injected_concerns=[("requirements_coverage", "unrelated lens")],  # missed
    )
    adjudication = {(0, 0, i): "spurious" for i in range(4)}
    recs = recommend_sensitivity(
        [AdjudicationReport(runs=[run])], adjudication=adjudication,
    )
    assert recs[0].direction is SensitivityDirection.INCREASE


# ---------- Noise robustness across repeated runs -----------------------


def test_repeated_runs_increase_confidence():
    """FR-044 noise robustness: multiple reports = repeated runs.
    Confidence label scales: 1 = low, 2 = medium, 3+ = high."""
    def _ok_run():
        return _make_run(
            injector_name="trivial_rq",
            expected_lens="methodology",
            clean_concerns=[],
            injected_concerns=[("methodology", "caught")],
        )

    # 1 run.
    recs = recommend_sensitivity([AdjudicationReport(runs=[_ok_run()])])
    assert recs[0].confidence == "low"

    # 2 runs.
    recs = recommend_sensitivity([
        AdjudicationReport(runs=[_ok_run()]),
        AdjudicationReport(runs=[_ok_run()]),
    ])
    assert recs[0].confidence == "medium"

    # 3 runs.
    recs = recommend_sensitivity([
        AdjudicationReport(runs=[_ok_run()]),
        AdjudicationReport(runs=[_ok_run()]),
        AdjudicationReport(runs=[_ok_run()]),
    ])
    assert recs[0].confidence == "high"


def test_transient_miss_across_runs_still_increases():
    """One missed run + two caught runs → still INCREASE (the floor is
    violated; the maintainer can use the medium-confidence signal to
    decide)."""
    caught_run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[],
        injected_concerns=[("methodology", "caught")],
    )
    missed_run = _make_run(
        injector_name="trivial_rq",
        expected_lens="methodology",
        clean_concerns=[],
        injected_concerns=[("requirements_coverage", "wrong lens")],
    )
    recs = recommend_sensitivity([
        AdjudicationReport(runs=[caught_run]),
        AdjudicationReport(runs=[caught_run]),
        AdjudicationReport(runs=[missed_run]),
    ])
    assert recs[0].direction is SensitivityDirection.INCREASE
    assert recs[0].caught_count == 2
    assert recs[0].missed_count == 1
    assert recs[0].confidence == "high"


# ---------- Configurable thresholds -------------------------------------


def test_miss_threshold_can_tolerate_one_transient_miss():
    """With miss_threshold=2, a single transient miss is STABLE."""
    caught_run = _make_run(
        injector_name="x", expected_lens="methodology", clean_concerns=[],
        injected_concerns=[("methodology", "caught")],
    )
    missed_run = _make_run(
        injector_name="x", expected_lens="methodology", clean_concerns=[],
        injected_concerns=[],
    )
    recs = recommend_sensitivity(
        [AdjudicationReport(runs=[caught_run, caught_run, missed_run])],
        miss_threshold=2,
    )
    assert recs[0].direction is SensitivityDirection.STABLE


def test_spurious_threshold_is_configurable():
    """spurious_extras_threshold=1 makes the recommender stricter."""
    run = _make_run(
        injector_name="x", expected_lens="methodology",
        clean_concerns=[("methodology", "nit")],
        injected_concerns=[("methodology", "caught")],
    )
    recs = recommend_sensitivity(
        [AdjudicationReport(runs=[run])],
        adjudication={(0, 0, 0): "spurious"},
        spurious_extras_threshold=1,
    )
    assert recs[0].direction is SensitivityDirection.REDUCE


# ---------- Rendering ---------------------------------------------------


def test_render_recommendations_markdown_lists_each_lens():
    run = _make_run(
        injector_name="x", expected_lens="methodology", clean_concerns=[],
        injected_concerns=[("methodology", "caught")],
    )
    recs = recommend_sensitivity([AdjudicationReport(runs=[run])])
    md = render_recommendations_markdown(recs, panel="plan")
    assert "panel: plan" in md
    assert "methodology" in md
    assert "STABLE" in md or "stable" in md
    # FR-044 reference present
    assert "FR-044" in md


def test_render_handles_empty_recommendations():
    md = render_recommendations_markdown([], panel="plan")
    assert "No recommendations" in md
