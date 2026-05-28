"""Integration tests for the scheduler's idempotency rule
(spec 015 T042 / FR-034).

The 3 spec-012 transient stages (PAPER_REVISION_IN_PROGRESS,
READY_FOR_IMPLEMENTATION, PAPER_REVISION_BLOCKED) were DELETED. The
new generic :class:`Stage.AGENT_BLOCKED` is the unified failsafe sink
the scheduler must skip; everything else routes through PAPER_REVIEW /
RESEARCH_REVIEW with a non-empty ``revision_spec_path`` (which IS
pickable — the implementer agent consumes those projects).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.pipeline.scheduler import _NEVER_PICK, pick_next
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _save_project(repo: Path, project_id: str, *, stage: Stage) -> Project:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    project = Project(
        id=project_id,
        title=f"Test {project_id}",
        field="computer science",
        current_stage=stage,
        created_at=now - timedelta(days=1),
        updated_at=now,
    )
    project_store.save(project, repo_root=repo)
    return project


class TestSchedulerIdempotency:
    def test_agent_blocked_is_in_never_pick(self) -> None:
        """The new generic AGENT_BLOCKED failsafe sink MUST be in
        _NEVER_PICK so the operator gets a chance to edit the action
        items before the scheduler re-picks the project."""
        assert Stage.AGENT_BLOCKED in _NEVER_PICK
        assert Stage.PUBLISH_BLOCKED in _NEVER_PICK
        assert Stage.HUMAN_INPUT_NEEDED in _NEVER_PICK
        assert Stage.BLOCKED in _NEVER_PICK
        # PAPER_REVIEW + RESEARCH_REVIEW MUST be pickable (the
        # implementer + reviewer agents consume them).
        assert Stage.PAPER_REVIEW not in _NEVER_PICK
        assert Stage.RESEARCH_REVIEW not in _NEVER_PICK

    def test_blocked_project_not_picked_over_runnable(self, tmp_path: Path) -> None:
        """Pick a project at AGENT_BLOCKED and one at BRAINSTORMED; the
        runnable one MUST be selected."""
        _save_project(tmp_path, "PROJ-100-locked", stage=Stage.AGENT_BLOCKED)
        _save_project(tmp_path, "PROJ-200-runnable", stage=Stage.BRAINSTORMED)
        picked = pick_next(repo_root=tmp_path)
        assert picked is not None
        assert picked.id == "PROJ-200-runnable"

    def test_only_blocked_returns_none(self, tmp_path: Path) -> None:
        """If every project is in a _NEVER_PICK state, pick_next returns
        None."""
        _save_project(tmp_path, "PROJ-100-a", stage=Stage.AGENT_BLOCKED)
        _save_project(tmp_path, "PROJ-200-b", stage=Stage.PUBLISH_BLOCKED)
        _save_project(tmp_path, "PROJ-300-c", stage=Stage.BLOCKED)
        picked = pick_next(repo_root=tmp_path)
        assert picked is None
