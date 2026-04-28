"""Integration test (T060): scheduler honors FR-001 priority order.

Pure file-fixture-driven; no LLM calls. Asserts:
  1. `in_progress` is preferred over `analyzed`.
  2. Within a tier, oldest `updated_at` wins.
  3. Locked projects are skipped.
  4. Projects in `human_input_needed` / `blocked` / `posted` are
     never returned.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llmxive.pipeline import lock as lockmod
from llmxive.pipeline import scheduler
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


_RESEARCH_STAGES_NEEDING_DIR = {
    Stage.SPECIFIED, Stage.CLARIFY_IN_PROGRESS, Stage.CLARIFIED,
    Stage.PLANNED, Stage.TASKED, Stage.ANALYZE_IN_PROGRESS, Stage.ANALYZED,
    Stage.IN_PROGRESS, Stage.RESEARCH_COMPLETE,
}
_PAPER_STAGES_NEEDING_DIR = {
    Stage.PAPER_SPECIFIED, Stage.PAPER_CLARIFIED, Stage.PAPER_PLANNED,
    Stage.PAPER_TASKED, Stage.PAPER_ANALYZED, Stage.PAPER_IN_PROGRESS,
    Stage.PAPER_COMPLETE,
}


def _make(repo: Path, project_id: str, stage: Stage, *, age_days: int = 0) -> Project:
    now = datetime.now(timezone.utc) - timedelta(days=age_days)
    kwargs: dict[str, object] = {
        "id": project_id,
        "title": project_id,
        "field": "test",
        "current_stage": stage,
        "points_research": {},
        "points_paper": {},
        "created_at": now,
        "updated_at": now,
        "artifact_hashes": {},
    }
    if stage in _RESEARCH_STAGES_NEEDING_DIR:
        kwargs["speckit_research_dir"] = f"projects/{project_id}/specs/001-test"
    if stage in _PAPER_STAGES_NEEDING_DIR:
        kwargs["speckit_research_dir"] = f"projects/{project_id}/specs/001-test"
        kwargs["speckit_paper_dir"] = f"projects/{project_id}/paper/specs/001-paper"
    if stage == Stage.HUMAN_INPUT_NEEDED:
        kwargs["human_escalation_reason"] = "fixture"
    p = Project(**kwargs)  # type: ignore[arg-type]
    project_store.save(p, repo_root=repo)
    return p


def _bootstrap_state(repo: Path) -> None:
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)


def test_in_progress_preempts_analyzed(tmp_path: Path) -> None:
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-001-fresh", Stage.ANALYZED, age_days=10)
    _make(tmp_path, "PROJ-002-active", Stage.IN_PROGRESS, age_days=1)

    picked = scheduler.pick_next(repo_root=tmp_path)
    assert picked is not None
    assert picked.id == "PROJ-002-active", (
        f"in_progress should preempt analyzed; got {picked.id}"
    )


def test_oldest_updated_at_wins_within_tier(tmp_path: Path) -> None:
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-100-newest", Stage.ANALYZED, age_days=1)
    _make(tmp_path, "PROJ-101-oldest", Stage.ANALYZED, age_days=20)
    _make(tmp_path, "PROJ-102-middle", Stage.ANALYZED, age_days=10)

    picked = scheduler.pick_next(repo_root=tmp_path)
    assert picked is not None and picked.id == "PROJ-101-oldest"


def test_locked_projects_skipped(tmp_path: Path) -> None:
    _bootstrap_state(tmp_path)
    p = _make(tmp_path, "PROJ-200-locked", Stage.IN_PROGRESS, age_days=5)
    _make(tmp_path, "PROJ-201-free", Stage.ANALYZED, age_days=10)
    lockmod.acquire(p.id, holder_run_id="other-run", ttl_seconds=3600, repo_root=tmp_path)

    picked = scheduler.pick_next(repo_root=tmp_path)
    assert picked is not None
    assert picked.id == "PROJ-201-free", "locked in_progress should be skipped"


@pytest.mark.parametrize("stage", [Stage.HUMAN_INPUT_NEEDED, Stage.BLOCKED, Stage.POSTED])
def test_excluded_stages_never_picked(tmp_path: Path, stage: Stage) -> None:
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-300-stuck", stage, age_days=1)
    _make(tmp_path, "PROJ-301-ready", Stage.IN_PROGRESS, age_days=10)

    picked = scheduler.pick_next(repo_root=tmp_path)
    assert picked is not None and picked.id == "PROJ-301-ready"


def test_full_priority_order(tmp_path: Path) -> None:
    """Plant one project at each priority tier; assert the highest-priority is picked."""
    _bootstrap_state(tmp_path)
    # Fill in only a subset of tiers (full enum is too large to test
    # exhaustively in one pass). Pick three points along the order.
    _make(tmp_path, "PROJ-401-clarified", Stage.CLARIFIED, age_days=1)
    _make(tmp_path, "PROJ-402-brainstormed", Stage.BRAINSTORMED, age_days=1)
    _make(tmp_path, "PROJ-403-paper-progress", Stage.PAPER_IN_PROGRESS, age_days=1)
    # The highest-priority among these (per the PRIORITY list) is CLARIFIED
    # — IN_PROGRESS / ANALYZED tiers are empty.
    picked = scheduler.pick_next(repo_root=tmp_path)
    assert picked is not None and picked.id == "PROJ-401-clarified"
