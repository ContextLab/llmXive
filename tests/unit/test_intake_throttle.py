"""Regression: automatic intake throttling (spec 023 / FR-008).

Real state files in a hermetic repo: project rows under
``state/projects/`` define the backlog; throttle decisions persist to the
observable ``state/intake_throttle.yaml``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from llmxive.pipeline import intake_throttle as it
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

_T0 = datetime(2026, 6, 10, 0, 0, 0, tzinfo=UTC)


def _seed_backlog(repo: Path, n: int, *, start: int = 0) -> None:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    for i in range(start, start + n):
        p = Project(
            id=f"PROJ-{6000 + i}-idea",
            title=f"idea {i}",
            field="test",
            current_stage=Stage.FLESH_OUT_COMPLETE,
            created_at=_T0,
            updated_at=_T0,
            artifact_hashes={},
        )
        project_store.save(p, repo_root=repo)


def test_cold_start_allows_full_intake(tmp_path: Path) -> None:
    _seed_backlog(tmp_path, 10)
    d = it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    assert d.allowed == 5
    assert not d.throttled
    # The decision is observable on disk.
    state = yaml.safe_load(
        (tmp_path / "state" / "intake_throttle.yaml").read_text()
    )
    assert state["last_decision"]["allowed"] == 5
    assert state["samples"], "the backlog sample is recorded"


def test_growing_backlog_throttles_proportionally(tmp_path: Path) -> None:
    _seed_backlog(tmp_path, 10)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    # Backlog grows by 10 within the window → allowance halves
    # (10 / FULL_STOP_GROWTH=20 → damped to 50%).
    _seed_backlog(tmp_path, 10, start=100)
    d = it.intake_allowance(5, repo_root=tmp_path, now=_T0 + timedelta(hours=2))
    assert d.growth == 10
    assert d.allowed == 2  # int(5 * 0.5)
    assert d.throttled
    assert "drain < intake" in d.reason


def test_runaway_growth_stops_auto_intake_entirely(tmp_path: Path) -> None:
    _seed_backlog(tmp_path, 10)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    _seed_backlog(tmp_path, it.FULL_STOP_GROWTH + 5, start=200)
    d = it.intake_allowance(5, repo_root=tmp_path, now=_T0 + timedelta(hours=3))
    assert d.allowed == 0


def test_throttle_recovers_when_backlog_drains(tmp_path: Path) -> None:
    """Proportional and self-recovering — never a permanent starve."""
    _seed_backlog(tmp_path, 10)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    _seed_backlog(tmp_path, 30, start=300)
    blocked = it.intake_allowance(
        5, repo_root=tmp_path, now=_T0 + timedelta(hours=2)
    )
    assert blocked.allowed == 0
    # Backlog drains: validated projects leave the idea stages.
    for p in project_store.list_all(repo_root=tmp_path)[:35]:
        project_store.save(
            p.model_copy(update={"current_stage": Stage.VALIDATED}),
            repo_root=tmp_path,
        )
    recovered = it.intake_allowance(
        5, repo_root=tmp_path, now=_T0 + timedelta(hours=4)
    )
    assert recovered.allowed == 5, "full intake resumes once draining"


def test_human_intake_never_throttled_to_zero(tmp_path: Path) -> None:
    _seed_backlog(tmp_path, 10)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    _seed_backlog(tmp_path, it.FULL_STOP_GROWTH + 10, start=400)
    d = it.intake_allowance(
        4, repo_root=tmp_path, kind="human", now=_T0 + timedelta(hours=2)
    )
    assert d.allowed >= it.MIN_HUMAN_ALLOWANCE


def test_window_expires_old_samples(tmp_path: Path) -> None:
    """Samples older than the window drop out — growth is measured over
    the window, not all of history."""
    _seed_backlog(tmp_path, 10)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    _seed_backlog(tmp_path, 50, start=500)
    # Two days later (old sample expired) and the backlog is now FLAT.
    d = it.intake_allowance(
        5, repo_root=tmp_path, now=_T0 + timedelta(hours=49)
    )
    assert d.growth == 0
    assert d.allowed == 5
