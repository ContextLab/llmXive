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
    assert "idea-backlog" in d.reason  # the binding constraint is named


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


def _seed_stage(repo: Path, n: int, stage: Stage, *, start: int) -> None:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    for i in range(start, start + n):
        pid = f"PROJ-{6000 + i}-x"
        project_store.save(
            Project(
                id=pid, title=f"p{i}", field="test",
                current_stage=stage, created_at=_T0, updated_at=_T0,
                artifact_hashes={},
                # required from 'specified' onward (in_progress/planned/tasked/…)
                speckit_research_dir=f"projects/{pid}/specs/001-x",
            ),
            repo_root=repo,
        )


def test_growing_downstream_wip_throttles_even_with_flat_idea_backlog(tmp_path: Path) -> None:
    """issue #1139 M1: the throttle was BLIND to the implementation pipeline. Even
    with a FLAT idea backlog, a growing downstream WIP (in_progress filling faster
    than it drains) must damp auto-intake."""
    _seed_backlog(tmp_path, 10)  # flat idea backlog
    _seed_stage(tmp_path, 5, Stage.IN_PROGRESS, start=1000)
    it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    # idea backlog stays flat; downstream WIP grows by DOWNSTREAM_FULL_STOP_GROWTH/2.
    _seed_stage(tmp_path, it.DOWNSTREAM_FULL_STOP_GROWTH // 2, Stage.IN_PROGRESS, start=2000)
    d = it.intake_allowance(5, repo_root=tmp_path, now=_T0 + timedelta(hours=2))
    assert d.growth == 0, "idea backlog is flat"
    assert d.allowed < 5, "growing downstream WIP must damp auto-intake"
    assert "downstream-WIP" in d.reason


def test_downstream_wip_ceiling_stops_auto_intake(tmp_path: Path) -> None:
    """A congested implementation pipeline above the ceiling damps auto-intake to
    zero regardless of growth — it must DRAIN before more ideas enter."""
    _seed_backlog(tmp_path, 5)  # small, flat idea backlog
    _seed_stage(tmp_path, it.DOWNSTREAM_WIP_CEILING * 2, Stage.IN_PROGRESS, start=3000)
    d = it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    assert d.allowed == 0, "auto-intake stops when downstream WIP is 2x the ceiling"
    assert "downstream-WIP-ceiling" in d.reason
    # Human intake is still floored.
    h = it.intake_allowance(4, repo_root=tmp_path, kind="human", now=_T0)
    assert h.allowed >= it.MIN_HUMAN_ALLOWANCE


def test_downstream_wip_ceiling_is_self_recovering(tmp_path: Path) -> None:
    """Once the pipeline drains back under the ceiling, full auto-intake resumes."""
    _seed_backlog(tmp_path, 5)
    _seed_stage(tmp_path, it.DOWNSTREAM_WIP_CEILING * 2, Stage.IN_PROGRESS, start=4000)
    blocked = it.intake_allowance(5, repo_root=tmp_path, now=_T0)
    assert blocked.allowed == 0
    # Drain: projects reach research_complete (leave the WIP stages).
    for p in project_store.list_all(repo_root=tmp_path):
        if p.current_stage == Stage.IN_PROGRESS:
            project_store.save(
                p.model_copy(update={"current_stage": Stage.RESEARCH_COMPLETE}),
                repo_root=tmp_path,
            )
    recovered = it.intake_allowance(5, repo_root=tmp_path, now=_T0 + timedelta(hours=2))
    assert recovered.allowed == 5, "full intake resumes once WIP drains under the ceiling"
