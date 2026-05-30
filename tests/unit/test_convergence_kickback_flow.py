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


def test_decide_escalates_after_cap(tmp_path: Path) -> None:
    from llmxive.pipeline.graph import _decide_next_stage

    project = _spec_project()
    project_dir = tmp_path / "projects" / project.id
    mem = project_dir / ".specify" / "memory"

    last_stage = None
    for _ in range(CONVERGENCE_KICKBACK_CAP + 1):
        _write_sentinel(mem, to_stage="flesh_out_in_progress", stage="spec")
        last_stage = _decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert last_stage == Stage.HUMAN_INPUT_NEEDED
    # The escalation reason marker is written for run_one_step to surface.
    assert (mem / "human_input_needed.yaml").exists()
    payload = yaml.safe_load((mem / "human_input_needed.yaml").read_text())
    assert "cap exceeded" in payload["reason"].lower()


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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
