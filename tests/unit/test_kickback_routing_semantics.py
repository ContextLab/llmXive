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
    EVERY stage the panel runs at and (b) a stage the graph can dispatch.

    Spec 023 defect #22: the tasks / paper-tasks panels run at TWO stages
    (the tasker drives both the planned and the tasked/analyze passes), so
    each route must be reachable from BOTH — the original single-run-stage
    check missed TASKED -> CLARIFIED, and a live kickback from tasked
    burned a full panel run then died on "invalid transition".
    """
    run_stages_by_label = {
        "plan": [Stage.CLARIFIED],
        "tasks": [Stage.PLANNED, Stage.TASKED],
        "paper_plan": [Stage.PAPER_CLARIFIED],
        "paper_tasks": [Stage.PAPER_PLANNED, Stage.PAPER_TASKED],
        "spec": [Stage.SPECIFIED],
        "paper_spec": [Stage.PAPER_SPECIFIED],
    }
    checked = 0
    for label, spec in _all_static_specs().items():
        for run_stage in run_stages_by_label[label]:
            for sev, target in spec.kickback_routing.items():
                target_stage = Stage(target)
                # A stay-put route (target == the stage the panel runs at) is a
                # no-op transition: graph.run_one_step only validates/applies a
                # transition when next_stage != current_stage, so the same
                # stage's agent simply re-runs next tick (spec 023 defect #19 —
                # in-place revision instead of regeneration).
                if target_stage != run_stage:
                    assert is_valid_transition(run_stage, target_stage), (
                        f"{label} panel {sev}: {run_stage.value} -> {target} is "
                        "not an allowed lifecycle transition"
                    )
                assert target_stage in STAGE_TO_AGENT, (
                    f"{label} panel {sev}: target {target} has no dispatchable agent"
                )
                checked += 1
    assert checked >= 34, f"only {checked} routes checked"


def test_full_revision_kickback_resets_revision_round_budget(tmp_path):
    """A FULL-revision kickback (research_full_revision → IN_PROGRESS) must CLEAR
    the project's revision-round budget so the redone analysis gets a fresh
    review cycle. research_full_revision is not a resting step — it kicks back to
    IMPLEMENTATION to re-do the analysis (under the fabrication-gated execution
    gate), not all the way to clarified. Without the reset the project returns to
    research_review already at the 3-round cap → kicks back again → loops to human
    escalation, never addressing concerns that surface only after the early rounds
    (PROJ-552's layered-review stall: rounds 1-3 on placeholder docs, the real
    data-quality defect at round 4)."""
    from datetime import UTC, datetime

    import yaml

    from llmxive.pipeline.graph import _decide_next_stage
    from llmxive.types import Project, Stage

    pid = "PROJ-942-knot"
    repo = tmp_path
    # pre-existing exhausted revision state
    ar = repo / "specs" / "auto-revisions" / pid
    (ar / "round-3").mkdir(parents=True)
    (ar / "round-3" / "tasks.md").write_text("x", encoding="utf-8")
    hist = repo / "projects" / pid / "paper"
    hist.mkdir(parents=True)
    (hist / "revision_history.yaml").write_text(
        yaml.safe_dump({"project_id": pid, "rounds": [{"round_number": n} for n in (1, 2, 3)]}),
        encoding="utf-8",
    )
    proj = Project(
        id=pid, title="t", field="t", current_stage=Stage.RESEARCH_FULL_REVISION,
        created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        artifact_hashes={}, speckit_research_dir=f"projects/{pid}/specs/001-t",
    )
    nxt = _decide_next_stage(proj, repo / "projects" / pid, repo_root=repo)
    assert nxt == Stage.IN_PROGRESS
    assert not (ar).exists(), "auto-revisions rounds must be cleared on full-revision kickback"
    assert not (hist / "revision_history.yaml").exists(), "revision_history must be cleared"
