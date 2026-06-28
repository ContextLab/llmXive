"""Adaptive convergence-kickback flow tests (F-14 / F-20 Part B).

Covers the three parts of the fix:

1. ``_stage_panel`` writes the ADAPTIVE ``convergence_kickback.yaml`` sentinel
   (not ``human_input_needed.yaml``) on a panel non-convergence kickback, but
   STILL writes ``human_input_needed.yaml`` on a genuine engine exception; and
   persists a per-round ``convergence_trail/`` JSONL provenance file.
2. ``graph._decide_next_stage`` consumes ``convergence_kickback.yaml`` → routes
   to its ``to_stage`` (deleting the sentinel), with a per-stage kickback cap
   that escalates to ``human_input_needed`` and resets on advancement.
3. The engine ``on_round`` hook persists a multi-round inspection trail.

No mocks of the unit under test — the ``_kickback`` helper + graph routing run
for real against on-disk sentinels; the ``_stage_panel`` tests use a constructed
fake ReviewSpec/backend (the established offline-engine fixture pattern), never a
mock of ``run_stage_panel`` / ``_decide_next_stage`` themselves.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from llmxive.pipeline._kickback import (
    CONVERGENCE_KICKBACK_CAP,
    consume_convergence_kickback,
    reset_kickback_count,
)
from llmxive.types import Project, Stage

# --- _kickback helper -----------------------------------------------------


def _write_sentinel(memory_dir: Path, *, to_stage: str, stage: str = "spec") -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "convergence_kickback.yaml").write_text(
        yaml.safe_dump(
            {
                "to_stage": to_stage,
                "worst_severity": "science",
                "reason": "did not converge",
                "stage": stage,
                "unresolved_concerns": [],
                "artifact_links": [],
            }
        ),
        encoding="utf-8",
    )


def test_consume_returns_none_when_no_sentinel(tmp_path: Path) -> None:
    assert consume_convergence_kickback(tmp_path) is None


def test_consume_routes_and_deletes_sentinel(tmp_path: Path) -> None:
    _write_sentinel(tmp_path, to_stage="flesh_out_in_progress")
    decision = consume_convergence_kickback(tmp_path)
    assert decision is not None
    assert decision.escalate is False
    assert decision.to_stage == "flesh_out_in_progress"
    assert decision.count == 1
    # Sentinel consumed.
    assert not (tmp_path / "convergence_kickback.yaml").exists()
    # Counter persisted.
    counts = yaml.safe_load((tmp_path / "kickback_count.yaml").read_text())
    assert counts == {"spec": 1}


def test_consume_escalates_past_cap(tmp_path: Path) -> None:
    decisions = []
    for _ in range(CONVERGENCE_KICKBACK_CAP + 1):
        _write_sentinel(tmp_path, to_stage="flesh_out_in_progress")
        decisions.append(consume_convergence_kickback(tmp_path))
    # The first CAP kickbacks route normally.
    for d in decisions[:CONVERGENCE_KICKBACK_CAP]:
        assert d is not None and d.escalate is False
    # The one that pushes count strictly above the cap escalates.
    last = decisions[-1]
    assert last is not None
    assert last.escalate is True
    assert last.to_stage is None
    assert last.count == CONVERGENCE_KICKBACK_CAP + 1
    # Counter is reset after escalation (human now owns the loop).
    assert not (tmp_path / "kickback_count.yaml").exists()


def test_malformed_to_stage_escalates(tmp_path: Path) -> None:
    _write_sentinel(tmp_path, to_stage="")
    decision = consume_convergence_kickback(tmp_path)
    assert decision is not None
    assert decision.escalate is True


def test_reset_kickback_count(tmp_path: Path) -> None:
    _write_sentinel(tmp_path, to_stage="flesh_out_in_progress", stage="spec")
    consume_convergence_kickback(tmp_path)
    assert yaml.safe_load((tmp_path / "kickback_count.yaml").read_text()) == {"spec": 1}
    reset_kickback_count(tmp_path, "spec")
    assert not (tmp_path / "kickback_count.yaml").exists()


# --- graph._decide_next_stage ---------------------------------------------


def _spec_project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id="PROJ-901-spec-kickback",
        title="X",
        field="mathematics",
        current_stage=Stage.SPECIFIED,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def test_decide_routes_convergence_kickback(tmp_path: Path) -> None:
    from llmxive.pipeline.graph import _decide_next_stage

    project = _spec_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")

    next_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert next_stage == Stage.FLESH_OUT_IN_PROGRESS
    # Sentinel consumed.
    assert not (mem / "convergence_kickback.yaml").exists()


def test_decide_escalates_model_tier_at_cap_then_replans(tmp_path: Path) -> None:
    """AUTONOMOUS exhaustion (mirrors the execution path): a convergence panel
    NEVER parks at human_input_needed. At the kickback cap it BUMPS the model
    tier and re-enters the review loop (returns the current stage to retry with
    a stronger model); only when EVERY model tier is exhausted does it route to
    the stage-appropriate re-work stage (research → PLANNED) with a
    deterministic concerns report, resetting the tier + kickback count.

    This replaces the old assertion that the cap routed to HUMAN_INPUT_NEEDED —
    that park is exactly what the user-directed flow eliminates (human input is
    required ONLY for the publication DOI sign-off)."""
    from llmxive.pipeline.graph import _decide_next_stage
    from llmxive.state import execution_status

    project = _spec_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"

    # The default ladder has tiers 0..N-1; the cap-hit bumps to the next usable
    # tier each time and stays in the review loop, until no higher tier remains.
    n_tiers = len(execution_status.model_tier_ladder())
    assert n_tiers >= 2, "ladder must have at least a default + one escalation"

    # Drive the cap (CAP+1 kickbacks) once per tier-bump: each cap-hit escalates
    # the tier and returns the CURRENT stage (retry), NOT human_input_needed.
    for expected_tier in range(1, n_tiers):
        last_stage = None
        for _ in range(CONVERGENCE_KICKBACK_CAP + 1):
            _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")
            last_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
        assert last_stage == project.current_stage  # stayed in the review loop
        assert last_stage != Stage.HUMAN_INPUT_NEEDED
        assert execution_status.model_tier(project.id, repo_root=tmp_path) == expected_tier
        # No human marker is ever written.
        assert not (mem / "human_input_needed.yaml").exists()

    # Now the top tier is reached: the next cap-hit EXHAUSTS the ladder and
    # routes to the deterministic re-work stage (research → PLANNED).
    last_stage = None
    for _ in range(CONVERGENCE_KICKBACK_CAP + 1):
        _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")
        last_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert last_stage == Stage.PLANNED
    assert last_stage != Stage.HUMAN_INPUT_NEEDED
    # Deterministic re-plan report written to the planner's ingestion file.
    replan = (mem / "kickback_feedback.md").read_text()
    assert "Re-plan" in replan and "adjust the approach" in replan
    # Tier + kickback count reset for a clean re-plan.
    assert execution_status.model_tier(project.id, repo_root=tmp_path) == 0
    assert not (mem / "human_input_needed.yaml").exists()


def test_decide_paper_panel_replans_to_paper_planned(tmp_path: Path) -> None:
    """A PAPER-track panel that exhausts its model ladder re-plans at
    PAPER_PLANNED (not PLANNED, not human_input_needed)."""
    from llmxive.pipeline.graph import _decide_next_stage
    from llmxive.state import execution_status

    now = datetime.now(UTC)
    project = Project(
        id="PROJ-903-paper-kickback",
        title="X",
        field="mathematics",
        current_stage=Stage.PAPER_SPECIFIED,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
        speckit_paper_dir="paper/specs/001-x",
    )
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / "paper" / ".specify" / "memory"

    n_tiers = len(execution_status.model_tier_ladder())
    # Bump through every tier, then exhaust.
    for _ in range(n_tiers):
        for _ in range(CONVERGENCE_KICKBACK_CAP + 1):
            _write_sentinel(mem, to_stage="paper_drafting_init", stage="paper_spec")
            last_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert last_stage == Stage.PAPER_PLANNED
    assert last_stage != Stage.HUMAN_INPUT_NEEDED
    # Re-plan note written to the PAPER memory dir.
    assert (mem / "kickback_feedback.md").exists()
    assert not (mem / "human_input_needed.yaml").exists()


def test_decide_invalid_to_stage_routes_to_planned(tmp_path: Path) -> None:
    """A convergence kickback that names an INVALID stage is a ROUTING BUG, not
    a human matter: it routes to the safe deterministic re-work stage (research
    → PLANNED) with a re-plan note — NEVER human_input_needed."""
    from llmxive.pipeline.graph import _decide_next_stage

    project = _spec_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    # A non-empty but invalid stage name (empty would escalate via the cap path;
    # this exercises the Stage(...) ValueError branch).
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "convergence_kickback.yaml").write_text(
        yaml.safe_dump(
            {
                "to_stage": "not_a_real_stage",
                "worst_severity": "science",
                "reason": "did not converge",
                "stage": "spec",
                "unresolved_concerns": [],
                "artifact_links": [],
            }
        ),
        encoding="utf-8",
    )
    next_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert next_stage == Stage.PLANNED
    assert next_stage != Stage.HUMAN_INPUT_NEEDED
    assert (mem / "kickback_feedback.md").exists()
    assert not (mem / "human_input_needed.yaml").exists()


def test_decide_resets_counter_on_advance(tmp_path: Path) -> None:
    from llmxive.pipeline._kickback import _read_counts
    from llmxive.pipeline.graph import _decide_next_stage

    project = _spec_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"

    # One kickback accrues a count of 1 for the "spec" stage.
    _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")
    assert _decide_next_stage(project, project_dir, repo_root=tmp_path) == \
        Stage.FLESH_OUT_IN_PROGRESS
    assert _read_counts(mem) == {"spec": 1}

    # Now the spec panel CONVERGES (no sentinel) → the project advances forward
    # from SPECIFIED. _decide_next_stage must reset the "spec" counter.
    nxt = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert nxt == Stage.CLARIFIED  # normal forward transition
    assert _read_counts(mem) == {}


def test_kickback_transitions_are_valid() -> None:
    """The adaptive-kickback targets must be valid lifecycle transitions from
    the stage at which each panel runs (else run_one_step raises)."""
    from llmxive.agents.lifecycle import is_valid_transition

    assert is_valid_transition(Stage.SPECIFIED, Stage.FLESH_OUT_IN_PROGRESS)
    assert is_valid_transition(Stage.SPECIFIED, Stage.PROJECT_INITIALIZED)
    assert is_valid_transition(Stage.SPECIFIED, Stage.HUMAN_INPUT_NEEDED)
    assert is_valid_transition(Stage.CLARIFIED, Stage.CLARIFIED)
    assert is_valid_transition(Stage.PAPER_SPECIFIED, Stage.PAPER_DRAFTING_INIT)
    assert is_valid_transition(Stage.PAPER_SPECIFIED, Stage.CLARIFIED)
    assert is_valid_transition(Stage.PAPER_CLARIFIED, Stage.PAPER_CLARIFIED)
    # Tasks panels run at PLANNED / PAPER_PLANNED: a writing-only kickback
    # advances (forward), a deeper concern self-loops to re-task, and the cap
    # escalates to human input. All three must be valid transitions, else a
    # tasks-stage kickback crashes run_one_step's is_valid_transition guard.
    assert is_valid_transition(Stage.PLANNED, Stage.TASKED)
    assert is_valid_transition(Stage.PLANNED, Stage.PLANNED)
    assert is_valid_transition(Stage.PLANNED, Stage.HUMAN_INPUT_NEEDED)
    assert is_valid_transition(Stage.PAPER_PLANNED, Stage.PAPER_TASKED)
    assert is_valid_transition(Stage.PAPER_PLANNED, Stage.PAPER_PLANNED)
    assert is_valid_transition(Stage.PAPER_PLANNED, Stage.HUMAN_INPUT_NEEDED)


# --- run_one_step catches the panel's raise and ROUTES (the real bug) ------
#
# The _decide_next_stage tests above prove routing works ONCE REACHED. But the
# spec panel signals non-convergence by RAISING StagePanelKickback from inside
# the agent run (after writing the sentinel). Before the Part-7 fix that raise
# propagated straight out of run_one_step (caught only by the CLI as a FAIL), so
# _decide_next_stage was never reached: the sentinel was never consumed, the
# project looped at SPECIFIED forever, and the kickback cap never incremented.
# These two tests exercise the REAL run_one_step exception handling + the REAL
# _decide_next_stage/_kickback routing; only the panel agent + registry/store
# collaborators are substituted to inject the controlled signal.


def _stub_registry_entry(name: str):
    from types import SimpleNamespace

    return SimpleNamespace(
        prompt_path=Path("prompts/x.md"),
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="m",
        prompt_version="1.0.0",
        name=name,
    )


def test_run_one_step_catches_kickback_and_routes(tmp_path: Path, monkeypatch) -> None:
    from llmxive.pipeline import graph
    from llmxive.speckit._stage_panel import StagePanelKickback
    from llmxive.state import project as project_store

    project = _spec_project()
    mem = tmp_path / "projects" / project.id / ".specify" / "memory"

    class _KickbackAgent:
        def run(self, sk_ctx) -> None:
            _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")
            raise StagePanelKickback(
                "spec panel did not converge (kickback → flesh_out_in_progress)"
            )

    monkeypatch.setitem(graph._SPECKIT_AGENTS, "clarifier", _KickbackAgent)
    monkeypatch.setattr(
        graph.registry_loader, "get",
        lambda name, repo_root=None: _stub_registry_entry(name),
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)

    result = graph.run_one_step(project, repo_root=tmp_path)

    # Routed to the content stage — NOT looped at SPECIFIED, NOT raised.
    assert result.current_stage == Stage.FLESH_OUT_IN_PROGRESS
    # Sentinel consumed and the per-stage cap counter incremented.
    assert not (mem / "convergence_kickback.yaml").exists()
    assert yaml.safe_load((mem / "kickback_count.yaml").read_text()) == {"spec": 1}


def test_run_one_step_keeps_project_schedulable_on_engine_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """Spec 023 / FR-016 (supersedes the spec-015 route-to-human form of
    this test): an engine failure files a tracked issue inside the panel
    and the graph keeps the project AT ITS CURRENT STAGE — schedulable,
    retried on later ticks. It must neither crash the run nor park the
    project at HUMAN_INPUT_NEEDED."""
    from llmxive.pipeline import graph
    from llmxive.speckit._stage_panel import StagePanelEscalation
    from llmxive.state import project as project_store

    project = _spec_project()

    class _EscalationAgent:
        def run(self, sk_ctx) -> None:
            # The panel files the engine-failure issue itself (covered by
            # test_escalation_paths); here it just raises.
            raise StagePanelEscalation("spec panel engine failure: boom")

    monkeypatch.setitem(graph._SPECKIT_AGENTS, "clarifier", _EscalationAgent)
    monkeypatch.setattr(
        graph.registry_loader, "get",
        lambda name, repo_root=None: _stub_registry_entry(name),
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)

    result = graph.run_one_step(project, repo_root=tmp_path)

    assert result.current_stage == project.current_stage, (
        "engine failure must leave the project at its stage (FR-016)"
    )
    assert result.current_stage != Stage.HUMAN_INPUT_NEEDED


# --- tasks-stage adaptive kickback (research tasker now emits the sentinel) ---
#
# The research tasks panel runs at PLANNED via the engine bridge and previously
# SWALLOWED non-convergence (recorded converged:False in tasker_rounds.yaml and
# advanced anyway). It now emits the SAME convergence_kickback.yaml sentinel the
# spec/plan panels do (via the shared emit_convergence_kickback helper) and
# raises StagePanelKickback, so run_one_step routes it: a writing-only kickback
# advances to TASKED, a deeper concern self-loops to PLANNED to re-task.


def _planned_project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id="PROJ-902-tasks-kickback",
        title="X",
        field="mathematics",
        current_stage=Stage.PLANNED,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def test_emit_helper_writes_consumable_tasks_sentinel(tmp_path: Path) -> None:
    """The shared helper builds a sentinel keyed by the 'tasks' label that the
    real consume_convergence_kickback reads back identically."""
    from llmxive.convergence.types import Concern, KickbackRecord, Severity
    from llmxive.speckit._stage_panel import emit_convergence_kickback

    kb = KickbackRecord(
        from_stage="tasked",
        to_stage="planned",
        worst_severity=Severity.SCIENCE,
        unresolved_concerns=[
            Concern(id="c1", reviewer="coverage", severity=Severity.SCIENCE,
                    artifact="specs/001-x/tasks.md", location="T003", text="missing setup"),
        ],
        artifact_links=["specs/001-x/tasks.md"],
        reason="1 concern unresolved after 3 rounds",
    )
    mem = tmp_path / ".specify" / "memory"
    emit_convergence_kickback(mem, kb, stage_label="tasks")

    decision = consume_convergence_kickback(mem)
    assert decision is not None
    assert decision.escalate is False
    assert decision.to_stage == "planned"
    assert decision.stage_label == "tasks"
    counts = yaml.safe_load((mem / "kickback_count.yaml").read_text())
    assert counts == {"tasks": 1}  # independent per-stage cap


def test_decide_routes_tasks_kickback_self_loop(tmp_path: Path) -> None:
    from llmxive.pipeline.graph import _decide_next_stage

    project = _planned_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"
    _write_sentinel(mem, to_stage="planned", stage="tasks")

    # A deeper tasks concern self-loops to PLANNED (re-task) — NOT a crash.
    assert _decide_next_stage(project, project_dir, repo_root=tmp_path) == Stage.PLANNED
    assert not (mem / "convergence_kickback.yaml").exists()


def test_decide_resets_tasks_counter_on_advance(tmp_path: Path) -> None:
    from llmxive.pipeline._kickback import _read_counts
    from llmxive.pipeline.graph import _decide_next_stage

    project = _planned_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"

    _write_sentinel(mem, to_stage="planned", stage="tasks")
    assert _decide_next_stage(project, project_dir, repo_root=tmp_path) == Stage.PLANNED
    assert _read_counts(mem) == {"tasks": 1}

    # Tasks panel converges (no sentinel) → forward to TASKED + counter reset.
    nxt = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert nxt == Stage.TASKED
    assert _read_counts(mem) == {}


def test_run_one_step_catches_tasks_kickback_and_self_loops(
    tmp_path: Path, monkeypatch
) -> None:
    """The REAL run_one_step seam for the tasker: a non-converging tasks panel
    raises StagePanelKickback → run_one_step routes to the PLANNED self-loop
    (not advance to TASKED, not crash), and the 'tasks' cap increments."""
    from llmxive.pipeline import graph
    from llmxive.speckit._stage_panel import StagePanelKickback
    from llmxive.state import project as project_store

    project = _planned_project()
    mem = tmp_path / "projects" / project.id / ".specify" / "memory"

    class _KickbackTasker:
        def run(self, sk_ctx) -> None:
            _write_sentinel(mem, to_stage="planned", stage="tasks")
            raise StagePanelKickback("tasks panel did not converge (→ planned)")

    monkeypatch.setitem(graph._SPECKIT_AGENTS, "tasker", _KickbackTasker)
    monkeypatch.setattr(
        graph.registry_loader, "get",
        lambda name, repo_root=None: _stub_registry_entry(name),
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)

    result = graph.run_one_step(project, repo_root=tmp_path)

    assert result.current_stage == Stage.PLANNED  # self-loop, NOT advanced to TASKED
    assert not (mem / "convergence_kickback.yaml").exists()
    assert yaml.safe_load((mem / "kickback_count.yaml").read_text()) == {"tasks": 1}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
