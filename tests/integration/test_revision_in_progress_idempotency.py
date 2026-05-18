"""Integration test for the scheduler's idempotency rule on
PAPER_REVISION_IN_PROGRESS (spec 012 / FR-009).

When a project is at PAPER_REVISION_IN_PROGRESS the auto-plan revision
pipeline is mid-flight. The regular scheduler MUST skip this project
(it must NOT re-trigger the planner). This test exercises the scheduler
on a fixture set that mixes runnable and in-progress projects and
asserts the in-progress one is not picked.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llmxive.pipeline.scheduler import pick_next, _NEVER_PICK
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _save_project(repo: Path, project_id: str, *, stage: Stage) -> Project:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
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
    def test_paper_revision_in_progress_is_in_never_pick(self) -> None:
        """The scheduler's _NEVER_PICK set MUST include the three spec-012
        stages so paper_revision_in_progress (the in-flight auto-plan),
        ready_for_implementation (waiting for implementer agent), and
        paper_revision_blocked (waiting for human) are all skipped by the
        regular tick-scheduler."""
        assert Stage.PAPER_REVISION_IN_PROGRESS in _NEVER_PICK
        assert Stage.READY_FOR_IMPLEMENTATION in _NEVER_PICK
        assert Stage.PAPER_REVISION_BLOCKED in _NEVER_PICK

    def test_in_progress_project_not_picked_over_runnable(self, tmp_path: Path) -> None:
        """Pick a project at PAPER_REVISION_IN_PROGRESS and one at BRAINSTORMED;
        the runnable one MUST be selected. (This is the operational meaning
        of the idempotency guarantee.)"""
        _save_project(tmp_path, "PROJ-100-locked", stage=Stage.PAPER_REVISION_IN_PROGRESS)
        _save_project(tmp_path, "PROJ-200-runnable", stage=Stage.BRAINSTORMED)
        picked = pick_next(repo_root=tmp_path)
        assert picked is not None
        assert picked.id == "PROJ-200-runnable"

    def test_only_in_progress_returns_none(self, tmp_path: Path) -> None:
        """If every project is in a _NEVER_PICK state, pick_next returns
        None (the scheduler doesn't pick anything to advance)."""
        _save_project(tmp_path, "PROJ-100-locked-a", stage=Stage.PAPER_REVISION_IN_PROGRESS)
        _save_project(tmp_path, "PROJ-200-locked-b", stage=Stage.READY_FOR_IMPLEMENTATION)
        _save_project(tmp_path, "PROJ-300-locked-c", stage=Stage.PAPER_REVISION_BLOCKED)
        picked = pick_next(repo_root=tmp_path)
        assert picked is None
