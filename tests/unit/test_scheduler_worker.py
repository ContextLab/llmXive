"""Deterministic multi-worker selection (advance.yml matrix lane).

`scheduler.pick_for_worker(i, n)` fans N concurrent matrix jobs across the
top-weighted stages by round-robin, each taking a DISTINCT project, fully
deterministic at a given repo state — so 6 jobs at the same HEAD pick 6
distinct projects (no double-work). These are REAL fixtures (no mocks):
Project state YAMLs written to a tmp repo, read back through the same
project_store the production path uses.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.pipeline import scheduler
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _make(
    repo: Path, project_id: str, stage: Stage, *, age_days: float = 1.0
) -> Project:
    now = datetime.now(UTC) - timedelta(days=age_days)
    kwargs: dict[str, object] = {
        "id": project_id,
        "title": project_id,
        "field": "test",
        "current_stage": stage,
        "created_at": now,
        "updated_at": now,
        "artifact_hashes": {},
    }
    if stage in {Stage.IN_PROGRESS, Stage.RESEARCH_COMPLETE}:
        kwargs["speckit_research_dir"] = f"projects/{project_id}/specs/001-t"
    p = Project(**kwargs)  # type: ignore[arg-type]
    project_store.save(p, repo_root=repo)
    return p


def _population(tmp_path: Path) -> Path:
    """Several stages, varying pile sizes + ages so the stage weights differ
    and there are enough projects per stage to exercise round-robin depth."""
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    # A deep, very stale early-stage pile (high load-balance weight).
    for i in range(6):
        _make(tmp_path, f"PROJ-{1000 + i}-foc", Stage.FLESH_OUT_COMPLETE, age_days=30 + i)
    # A mid pile.
    for i in range(4):
        _make(tmp_path, f"PROJ-{2000 + i}-init", Stage.PROJECT_INITIALIZED, age_days=10 + i)
    # A small further-along pile.
    for i in range(3):
        _make(tmp_path, f"PROJ-{3000 + i}-impl", Stage.IN_PROGRESS, age_days=5 + i)
    # A tiny brainstorm pile.
    for i in range(2):
        _make(tmp_path, f"PROJ-{4000 + i}-brain", Stage.BRAINSTORMED, age_days=2 + i)
    # Terminal / never-pick stages that must be excluded.
    _make(tmp_path, "PROJ-5001-posted", Stage.POSTED, age_days=1)
    return tmp_path


def _ranked_stages(repo: Path) -> list[Stage]:
    cands = scheduler._eligible_candidates(repo_root=repo, stage=None)
    by_stage: dict[Stage, list[Project]] = {}
    for p in cands:
        by_stage.setdefault(p.current_stage, []).append(p)
    now = datetime.now(UTC)
    return sorted(
        by_stage,
        key=lambda s: (
            -scheduler.stage_weight(s, by_stage[s], now=now),
            -scheduler._stage_rank(s),
            s.value,
        ),
    )


def test_workers_pick_distinct_projects(tmp_path: Path) -> None:
    repo = _population(tmp_path)
    n = 6
    picks = [scheduler.pick_for_worker(i, n, repo_root=repo) for i in range(n)]
    assert all(p is not None for p in picks), picks
    ids = [p.id for p in picks if p is not None]
    assert len(ids) == len(set(ids)), f"workers double-picked: {ids}"


def test_worker_zero_lands_on_highest_weight_stalest(tmp_path: Path) -> None:
    repo = _population(tmp_path)
    ranked = _ranked_stages(repo)
    top_stage = ranked[0]
    p0 = scheduler.pick_for_worker(0, 6, repo_root=repo)
    assert p0 is not None
    assert p0.current_stage == top_stage
    # Within that stage worker 0 takes the STALEST (oldest updated_at) project.
    in_stage = [
        c for c in scheduler._eligible_candidates(repo_root=repo, stage=None)
        if c.current_stage == top_stage
    ]
    stalest = sorted(in_stage, key=lambda p: (p.updated_at, p.id))[0]
    assert p0.id == stalest.id


def test_determinism(tmp_path: Path) -> None:
    repo = _population(tmp_path)
    for i in range(6):
        a = scheduler.pick_for_worker(i, 6, repo_root=repo)
        b = scheduler.pick_for_worker(i, 6, repo_root=repo)
        assert (a is None) == (b is None)
        if a is not None and b is not None:
            assert a.id == b.id


def test_round_robin_wraps_to_depth(tmp_path: Path) -> None:
    """With more workers than stages, workers wrap back to the same stages but
    take a DEEPER (next-stalest) project — never the same one twice."""
    repo = _population(tmp_path)
    ranked = _ranked_stages(repo)
    n_stages = len(ranked)
    assert n_stages >= 2
    # worker 0 and worker n_stages both hit ranked[0], at depth 0 and depth 1.
    p0 = scheduler.pick_for_worker(0, n_stages * 3, repo_root=repo)
    p_wrap = scheduler.pick_for_worker(n_stages, n_stages * 3, repo_root=repo)
    assert p0 is not None and p_wrap is not None
    assert p0.current_stage == p_wrap.current_stage == ranked[0]
    assert p0.id != p_wrap.id
    in_top = sorted(
        [c for c in scheduler._eligible_candidates(repo_root=repo, stage=None)
         if c.current_stage == ranked[0]],
        key=lambda p: (p.updated_at, p.id),
    )
    assert p0.id == in_top[0].id
    assert p_wrap.id == in_top[1].id


def test_returns_none_past_the_end(tmp_path: Path) -> None:
    """When the round-robin depth exceeds a stage's project count, the worker
    gets None (rather than colliding with another worker's project)."""
    repo = _population(tmp_path)
    ranked = _ranked_stages(repo)
    n_stages = len(ranked)
    # Find the smallest stage (e.g. brainstormed with 2 projects). A worker
    # index that lands on it at a depth >= its count must return None.
    cands = scheduler._eligible_candidates(repo_root=repo, stage=None)
    counts: dict[Stage, int] = {}
    for c in cands:
        counts[c.current_stage] = counts.get(c.current_stage, 0) + 1
    small_stage = min(ranked, key=lambda s: counts[s])
    small_rank = ranked.index(small_stage)
    depth = counts[small_stage]  # one past the last valid depth
    worker_index = small_rank + depth * n_stages
    assert scheduler.pick_for_worker(worker_index, worker_index + 1, repo_root=repo) is None


def test_empty_repo_returns_none(tmp_path: Path) -> None:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    assert scheduler.pick_for_worker(0, 6, repo_root=tmp_path) is None


def test_terminal_stages_never_picked(tmp_path: Path) -> None:
    repo = _population(tmp_path)
    for i in range(12):
        p = scheduler.pick_for_worker(i, 12, repo_root=repo)
        if p is not None:
            assert p.current_stage not in scheduler._NEVER_PICK
