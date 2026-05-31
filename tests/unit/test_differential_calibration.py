"""Unit tests for the differential calibration harness (spec 015 T065).

Validates the pure data-processing layer that turns
clean-vs-injected ConvergenceResult pairs into a markdown adjudication
report — without needing the engine or any LLM.
"""

from __future__ import annotations

from llmxive.calibration.differential import (
    CalibrationRun,
    adjudicate,
)
from llmxive.calibration.injectors import (
    inject_circular_rq,
    inject_fr_without_task,
)
from llmxive.convergence.types import (
    Concern,
    ConvergenceResult,
    Severity,
)


def _result(
    *, stage: str, converged: bool, concerns: list[Concern]
) -> ConvergenceResult:
    return ConvergenceResult(
        stage=stage,
        converged=converged,
        rounds_used=1,
        concern_history=concerns,
    )


def test_calibration_run_caught_when_expected_lens_in_injected_concerns():
    """The injected run flagged the expected lens → caught=True."""
    inj = inject_circular_rq("Research question: x")
    clean = _result(stage="flesh_out_complete", converged=True, concerns=[])
    injected = _result(
        stage="flesh_out_complete", converged=False,
        concerns=[Concern(
            id="C1", reviewer="rq_validity", severity=Severity.SCIENCE,
            artifact="idea.md", location="", text="circular RQ",
        )],
    )
    run = CalibrationRun(
        injector_name="circular_rq", injection=inj,
        clean_result=clean, injected_result=injected,
    )
    assert run.expected_lens == "rq_validity"
    assert run.caught is True
    assert run.extra_findings_on_clean == []


def test_calibration_run_missed_when_expected_lens_not_in_injected():
    """The injected run did NOT flag the expected lens → caught=False
    (calibration miss)."""
    inj = inject_circular_rq("Research question: x")
    clean = _result(stage="flesh_out_complete", converged=True, concerns=[])
    # Injected run got flagged by SOME lens, just not rq_validity.
    injected = _result(
        stage="flesh_out_complete", converged=False,
        concerns=[Concern(
            id="C1", reviewer="novelty", severity=Severity.WRITING,
            artifact="idea.md", location="", text="weak novelty",
        )],
    )
    run = CalibrationRun(
        injector_name="circular_rq", injection=inj,
        clean_result=clean, injected_result=injected,
    )
    assert run.caught is False


def test_calibration_run_extra_findings_lists_clean_side_concerns():
    """Concerns surfaced on the CLEAN artifact go to the extra-findings
    list (each needs maintainer adjudication)."""
    inj = inject_fr_without_task("- T001 [FR-001]: do X")
    extra_concern = Concern(
        id="X1", reviewer="executability", severity=Severity.WRITING,
        artifact="tasks.md", location="T001",
        text="T001 description could be more specific",
    )
    clean = _result(
        stage="tasked", converged=False, concerns=[extra_concern],
    )
    injected = _result(
        stage="tasked", converged=False,
        concerns=[Concern(
            id="C1", reviewer="coverage", severity=Severity.REQUIREMENT,
            artifact="tasks.md", location="FR-999", text="orphaned FR",
        )],
    )
    run = CalibrationRun(
        injector_name="fr_without_task", injection=inj,
        clean_result=clean, injected_result=injected,
    )
    assert run.caught is True  # coverage was flagged
    assert len(run.extra_findings_on_clean) == 1
    assert run.extra_findings_on_clean[0].reviewer == "executability"


def test_adjudication_report_aggregates_counts_correctly():
    inj = inject_circular_rq("Research question: x")
    clean = _result(stage="flesh_out_complete", converged=True, concerns=[])
    injected_caught = _result(
        stage="flesh_out_complete", converged=False,
        concerns=[Concern(
            id="C1", reviewer="rq_validity", severity=Severity.SCIENCE,
            artifact="idea.md", location="", text="circular",
        )],
    )
    injected_missed = _result(
        stage="flesh_out_complete", converged=True, concerns=[],
    )
    extra_concern = Concern(
        id="X1", reviewer="novelty", severity=Severity.WRITING,
        artifact="idea.md", location="", text="weak novelty signal",
    )
    clean_with_extra = _result(
        stage="flesh_out_complete", converged=False, concerns=[extra_concern],
    )
    runs = [
        CalibrationRun(injector_name="r1", injection=inj,
                       clean_result=clean, injected_result=injected_caught),
        CalibrationRun(injector_name="r2", injection=inj,
                       clean_result=clean_with_extra, injected_result=injected_missed),
        CalibrationRun(injector_name="r3", injection=inj,
                       clean_result=clean, injected_result=injected_caught),
    ]
    report = adjudicate(runs, domain="cognitive_neuroscience")
    assert report.caught_count == 2  # r1 + r3
    assert report.missed_count == 1  # r2
    assert report.total_extra_findings == 1  # from r2's clean


def test_adjudication_report_markdown_includes_every_run_section():
    inj = inject_circular_rq("Research question: x")
    clean = _result(stage="flesh_out_complete", converged=True, concerns=[])
    injected = _result(
        stage="flesh_out_complete", converged=False,
        concerns=[Concern(
            id="C1", reviewer="rq_validity", severity=Severity.SCIENCE,
            artifact="idea.md", location="", text="circular",
        )],
    )
    runs = [
        CalibrationRun(injector_name="circular_rq", injection=inj,
                       clean_result=clean, injected_result=injected),
    ]
    report = adjudicate(runs, domain="machine_learning")
    md = report.to_markdown(domain="machine_learning")
    assert "domain: machine_learning" in md
    assert "Injector: `circular_rq`" in md
    assert "✅ CAUGHT" in md
    # No-extra-finding case shows the success marker.
    assert "Clean artifact surfaced no concerns. ✅" in md


def test_adjudication_report_markdown_shows_adjudication_checklist_for_extras():
    inj = inject_circular_rq("Research question: x")
    extra_concern = Concern(
        id="X1", reviewer="novelty", severity=Severity.WRITING,
        artifact="idea.md", location="L5", text="prior work undercited",
    )
    clean = _result(
        stage="flesh_out_complete", converged=False, concerns=[extra_concern],
    )
    injected = _result(stage="flesh_out_complete", converged=True, concerns=[])
    runs = [
        CalibrationRun(injector_name="circular_rq", injection=inj,
                       clean_result=clean, injected_result=injected),
    ]
    md = adjudicate(runs).to_markdown()
    # The extra finding appears with reviewer + severity + location.
    assert "`novelty`" in md
    assert "[writing]" in md
    assert "L5" in md
    # And there's an adjudication checkbox line for each extra.
    assert "- [ ] 1.1: legitimate / spurious" in md


def test_adjudication_report_markdown_describes_design_principle():
    """The header MUST cite FR-046 + the differential + manual rule so
    a maintainer reading the report cold knows the adjudication contract."""
    md = adjudicate([]).to_markdown()
    assert "FR-046" in md
    assert "DIFFERENTIAL + manual" in md or "differential + manual" in md.lower()
    assert "no fixed over-flag" in md.lower()


def test_adjudication_report_empty_runs_renders_cleanly():
    md = adjudicate([]).to_markdown(domain="test")
    assert "0 of 0 injections caught" in md
