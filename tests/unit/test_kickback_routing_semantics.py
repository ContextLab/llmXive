"""Regression (spec 023 defect #14): kickback to_stage names the stage
whose AGENT must re-run — the graph dispatches STAGE_TO_AGENT[to_stage].

The old maps were one stage too far forward: the plan panel's "spec gap"
route ("clarified") re-ran the PLANNER against the same defective spec, so
a spec.md defect flagged at plan stage could never be repaired — observed
live on PROJ-552, which burned its whole kickback cap re-flagging a
spec.md factual error the plan reviser is structurally forbidden from
editing (it rejects writes outside the plan artifact set).
"""

from __future__ import annotations

from llmxive.agents.lifecycle import is_valid_transition
from llmxive.convergence import reviewspecs
from llmxive.convergence.types import Severity
from llmxive.pipeline.graph import STAGE_TO_AGENT
from llmxive.types import Stage


def _all_static_specs():
    return {
        "plan": reviewspecs._spec_research_plan(),
        "tasks": reviewspecs._spec_research_tasks(),
        "paper_plan": reviewspecs._spec_paper_plan(),
        "paper_tasks": reviewspecs._spec_paper_tasks(),
        "spec": reviewspecs._spec_research_spec(),
        "paper_spec": reviewspecs._spec_paper_spec(),
    }


def test_spec_gap_routes_rerun_the_artifact_owner():
    """For the four doc panels: every non-writing kickback target's agent
    must be the one that can actually revise the flagged artifact."""
    specs = _all_static_specs()

    plan = specs["plan"]
    for sev in (Severity.REQUIREMENT, Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert plan.kickback_routing[sev] == "specified", (
            f"plan panel {sev}: spec-gap kickbacks must re-run the spec "
            "panel (stage 'specified'), not the planner"
        )
    assert plan.kickback_routing[Severity.WRITING] == "clarified"

    tasks = specs["tasks"]
    for sev in (Severity.REQUIREMENT, Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert tasks.kickback_routing[sev] == "clarified", (
            f"tasks panel {sev}: plan-flaw kickbacks must re-run the planner"
        )

    paper_plan = specs["paper_plan"]
    for sev in (Severity.REQUIREMENT, Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert paper_plan.kickback_routing[sev] == "paper_specified"
    paper_tasks = specs["paper_tasks"]
    for sev in (Severity.REQUIREMENT, Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL):
        assert paper_tasks.kickback_routing[sev] == "paper_clarified"

    # Spec 023 defect #19: spec-panel doc-level residue revises IN PLACE
    # (stay-put re-dispatch of the clarifier) — never back through the
    # specifier, which regenerates a fresh specs/NNN dir.
    spec = specs["spec"]
    for sev in (Severity.WRITING, Severity.REQUIREMENT):
        assert spec.kickback_routing[sev] == "specified"
        assert spec.kickback_routing[sev] != "project_initialized"
    paper_spec = specs["paper_spec"]
    for sev in (Severity.WRITING, Severity.REQUIREMENT):
        assert paper_spec.kickback_routing[sev] == "paper_specified"
        assert paper_spec.kickback_routing[sev] != "paper_drafting_init"


def test_all_routes_are_valid_transitions_and_dispatchable():
    """Every routing target must be (a) a valid lifecycle transition from
    the stage the panel runs at and (b) a stage the graph can dispatch."""
    run_stage_by_label = {
        "plan": Stage.CLARIFIED,
        "tasks": Stage.PLANNED,
        "paper_plan": Stage.PAPER_CLARIFIED,
        "paper_tasks": Stage.PAPER_PLANNED,
        "spec": Stage.SPECIFIED,
        "paper_spec": Stage.PAPER_SPECIFIED,
    }
    checked = 0
    for label, spec in _all_static_specs().items():
        run_stage = run_stage_by_label[label]
        for sev, target in spec.kickback_routing.items():
            target_stage = Stage(target)
            # A stay-put route (target == the stage the panel runs at) is a
            # no-op transition: graph.run_one_step only validates/applies a
            # transition when next_stage != current_stage, so the same
            # stage's agent simply re-runs next tick (spec 023 defect #19 —
            # in-place revision instead of regeneration).
            if target_stage != run_stage:
                assert is_valid_transition(run_stage, target_stage), (
                    f"{label} panel {sev}: {run_stage.value} -> {target} is not "
                    "an allowed lifecycle transition"
                )
            assert target_stage in STAGE_TO_AGENT, (
                f"{label} panel {sev}: target {target} has no dispatchable agent"
            )
            checked += 1
    assert checked >= 24, f"only {checked} routes checked"
