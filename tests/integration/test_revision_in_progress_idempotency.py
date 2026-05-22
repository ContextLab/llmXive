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
        """_NEVER_PICK MUST include the still-locked revision states so the
        regular tick-scheduler skips them: paper_revision_in_progress (the
        in-flight auto-plan) and paper_revision_blocked (waiting for human).

        Spec 013 deliberately made READY_FOR_IMPLEMENTATION *pickable* — the
        `llmXive-implementer` agent (``agents/implementer.py``) consumes
        projects at that stage via the scheduler — so it MUST NOT be in
        _NEVER_PICK (this was an explicit out-of-scope item in spec 012 that
        spec 013 brought in scope)."""
        assert Stage.PAPER_REVISION_IN_PROGRESS in _NEVER_PICK
        assert Stage.PAPER_REVISION_BLOCKED in _NEVER_PICK
        assert Stage.READY_FOR_IMPLEMENTATION not in _NEVER_PICK

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
        None (the scheduler doesn't pick anything to advance). Uses only
        genuinely-locked stages — READY_FOR_IMPLEMENTATION is intentionally
        excluded here because spec 013 made it pickable (the implementer agent
        consumes it)."""
        _save_project(tmp_path, "PROJ-100-locked-a", stage=Stage.PAPER_REVISION_IN_PROGRESS)
        _save_project(tmp_path, "PROJ-200-locked-b", stage=Stage.PUBLISH_BLOCKED)
        _save_project(tmp_path, "PROJ-300-locked-c", stage=Stage.PAPER_REVISION_BLOCKED)
        picked = pick_next(repo_root=tmp_path)
        assert picked is None
