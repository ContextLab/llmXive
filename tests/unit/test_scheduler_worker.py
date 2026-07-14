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


# --- Workers are APPORTIONED by load, not round-robined one-per-stage ----------
#
# These two tests previously pinned the round-robin MECHANISM
# (`ranked_stages[i % len(ranked)]`, depth = `i // len(ranked)`). That mechanism was
# the bug: it used the stage weights only to ORDER the stages and threw their
# MAGNITUDE away, so a stage holding 433 projects (in_progress — 41% of the fleet)
# got exactly as many workers as a stage holding 1, and the biggest pile could never
# drain. A worker whose slot landed on a small stage at depth >= its count also
# picked NOTHING and idled — which the old `test_returns_none_past_the_end` asserted
# as correct.
#
# The contract is now: apportion the N workers across stages in PROPORTION to the
# load-balancing weight (overflow above equal share), capped by pile size and by
# MAX_STAGE_WORKER_SHARE. The invariants the old tests were really protecting —
# determinism, no double-work, stalest-first within a stage, and never
# over-assigning an exhausted stage — are pinned below, and more strictly (across
# ALL workers, not just two).


def test_repeat_slots_on_a_stage_take_deeper_projects(tmp_path: Path) -> None:
    """When a stage is apportioned several workers they take DISTINCT, successively
    staler projects — never the same one twice."""
    repo = _population(tmp_path)
    n = len(_ranked_stages(repo)) * 3
    picks = [scheduler.pick_for_worker(i, n, repo_root=repo) for i in range(n)]
    by_stage: dict[Stage, list[str]] = {}
    for p in picks:
        if p is not None:
            by_stage.setdefault(p.current_stage, []).append(p.id)
    # At least one stage must hold >1 worker (that is the point of apportionment).
    assert any(len(v) > 1 for v in by_stage.values()), by_stage
    for stage, ids in by_stage.items():
        assert len(ids) == len(set(ids)), f"double-work within {stage}"
        in_stage = sorted(
            [c for c in scheduler._eligible_candidates(repo_root=repo, stage=None)
             if c.current_stage == stage],
            key=lambda p: (p.updated_at, p.id),
        )
        # The k workers on a stage take its k stalest projects, stalest first.
        assert ids == [p.id for p in in_stage[:len(ids)]]


def test_no_worker_is_assigned_past_a_stage_pile(tmp_path: Path) -> None:
    """A stage is never assigned more workers than it has projects — so no worker
    collides with another's project, and none idles on an exhausted pile."""
    repo = _population(tmp_path)
    cands = scheduler._eligible_candidates(repo_root=repo, stage=None)
    counts: dict[Stage, int] = {}
    for c in cands:
        counts[c.current_stage] = counts.get(c.current_stage, 0) + 1
    # Ask for far more workers than there are projects: every returned pick must
    # still be a DISTINCT project, and the surplus workers get None.
    n = len(cands) + 5
    picks = [scheduler.pick_for_worker(i, n, repo_root=repo) for i in range(n)]
    got = [p.id for p in picks if p is not None]
    assert len(got) == len(set(got)), "double-work across workers"
    assert len(got) <= len(cands)
    assert picks[-1] is None  # surplus worker beyond the whole population
    per_stage: dict[Stage, int] = {}
    for p in picks:
        if p is not None:
            per_stage[p.current_stage] = per_stage.get(p.current_stage, 0) + 1
    for stage, k in per_stage.items():
        assert k <= counts[stage], f"{stage} over-assigned"


def test_biggest_pile_gets_the_most_workers_but_never_all(tmp_path: Path) -> None:
    """The load-balance policy made real: the most over-target stage takes the
    largest share of the matrix — but MAX_STAGE_WORKER_SHARE keeps it from taking
    every worker, so the stages feeding it are never fully starved (FR-006)."""
    repo = _population(tmp_path)
    cands = scheduler._eligible_candidates(repo_root=repo, stage=None)
    counts: dict[Stage, int] = {}
    for c in cands:
        counts[c.current_stage] = counts.get(c.current_stage, 0) + 1
    biggest = max(counts, key=lambda s: counts[s])
    n = 6
    picks = [scheduler.pick_for_worker(i, n, repo_root=repo) for i in range(n)]
    per_stage: dict[Stage, int] = {}
    for p in picks:
        if p is not None:
            per_stage[p.current_stage] = per_stage.get(p.current_stage, 0) + 1
    if counts[biggest] >= n:  # only meaningful when the pile can absorb the workers
        assert per_stage.get(biggest, 0) == max(per_stage.values())
        assert per_stage[biggest] < n, "one stage took EVERY worker (starvation)"
        assert len(per_stage) >= 2


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


def test_sparse_transient_stage_is_always_drained(tmp_path: Path) -> None:
    """A sparse transient routing stage (research_full_revision) has tiny
    load-balance weight and would rank below the worker count — so a worker never
    reaches it and the project is stranded FOREVER (PROJ-604 parked there: review
    correctly flagged full_revision, it routed to research_full_revision, then no
    worker ever picked that floor-weight stage to apply the -> in_progress
    routing). It MUST be floated to the front so a worker drains it every tick."""
    from datetime import UTC, datetime, timedelta

    repo = _population(tmp_path)  # high-weight piles, no transient stage
    now = datetime.now(UTC) - timedelta(days=1)
    parked = Project(
        id="PROJ-9001-fullrev", title="t", field="test",
        current_stage=Stage.RESEARCH_FULL_REVISION, created_at=now, updated_at=now,
        artifact_hashes={}, speckit_research_dir="projects/PROJ-9001-fullrev/specs/001-t",
    )
    project_store.save(parked, repo_root=repo)

    # Worker 0 (highest priority) must land on the transient stage.
    p0 = scheduler.pick_for_worker(0, 6, repo_root=repo)
    assert p0 is not None and p0.id == "PROJ-9001-fullrev", (
        f"transient routing stage must be drained first; worker 0 got "
        f"{p0.id if p0 else None} ({p0.current_stage.value if p0 else '-'})"
    )
    # And the 6 workers still pick DISTINCT projects (no double-work regression).
    picks = [scheduler.pick_for_worker(i, 6, repo_root=repo) for i in range(6)]
    ids = [p.id for p in picks if p is not None]
    assert len(ids) == len(set(ids)), f"workers double-picked: {ids}"


# --- in_progress is served SHORTEST-REMAINING first (completions, not sharing) ---
#
# Within a stage, projects were ordered stalest-`updated_at`-first. But working on a
# project REFRESHES its updated_at and sends it to the back — so in_progress became a
# strict round-robin across all 435 projects. Draining a project takes several ticks
# (~38 tasks at ~10/tick), so each one had to wait for the other 434 between touches
# and NOTHING ever completed: processor-sharing starvation, and the reason 0 projects
# had ever crossed research_complete. Implement stages now serve the project CLOSEST
# to done first, which converts the same effort into finished projects. It cannot
# starve the big ones: a completed project LEAVES the stage, so the queue advances.


def _impl_project(repo: Path, pid: str, *, open_tasks: int, age_days: float) -> None:
    _make(repo, pid, Stage.IN_PROGRESS, age_days=age_days)
    d = repo / "projects" / pid / "specs" / "001-t"
    d.mkdir(parents=True, exist_ok=True)
    lines = ["# Tasks", ""]
    lines += [f"- [X] T{i:03d} done work" for i in range(3)]
    lines += [f"- [ ] T{100 + i:03d} remaining work" for i in range(open_tasks)]
    (d / "tasks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_in_progress_serves_the_closest_to_done_first(tmp_path: Path) -> None:
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    # The near-done project is the FRESHEST (worked on most recently) — under the old
    # stalest-first order it would be picked LAST, which is exactly the bug.
    _impl_project(tmp_path, "PROJ-9001-almost", open_tasks=2, age_days=1)
    _impl_project(tmp_path, "PROJ-9002-midway", open_tasks=20, age_days=10)
    _impl_project(tmp_path, "PROJ-9003-barely", open_tasks=60, age_days=30)

    p0 = scheduler.pick_for_worker(0, 1, repo_root=tmp_path)
    assert p0 is not None and p0.id == "PROJ-9001-almost", p0

    # Successive workers walk outward: fewest-remaining first, then the rest.
    picks = [scheduler.pick_for_worker(i, 3, repo_root=tmp_path) for i in range(3)]
    got = [p.id for p in picks if p is not None]
    assert got == ["PROJ-9001-almost", "PROJ-9002-midway", "PROJ-9003-barely"], got


def test_non_implement_stages_still_ordered_by_staleness(tmp_path: Path) -> None:
    """The change is scoped to the implement stages — elsewhere oldest-waiting still
    wins (there is no 'remaining work' to be short of)."""
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    _make(tmp_path, "PROJ-9101-fresh", Stage.BRAINSTORMED, age_days=1)
    _make(tmp_path, "PROJ-9102-stale", Stage.BRAINSTORMED, age_days=40)
    p0 = scheduler.pick_for_worker(0, 1, repo_root=tmp_path)
    assert p0 is not None and p0.id == "PROJ-9102-stale", p0


def test_execution_churners_do_not_monopolise_the_matrix(tmp_path: Path) -> None:
    """A project stuck in the execution fix-loop is NOT 'nearly done'.

    Shortest-remaining-first sorts on open tasks — but a failed execution RE-OPENS
    only a handful of tasks, so a project whose analysis can never run sits at ~6
    remaining forever and is re-picked every single tick. On 2026-07-14 twelve such
    churners consumed ~4,000 of the day's 5,111 implementer calls (one took 843)
    while 400 projects got NONE, and only 2 crossed. Its accumulated failures must
    push it back so healthy work gets the workers — while still letting it come round
    again (it needs more attempts to reach the re-plan cap and be rejected).
    """
    from llmxive.state import execution_status as es

    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    _impl_project(tmp_path, "PROJ-9201-churner", open_tasks=6, age_days=1)
    _impl_project(tmp_path, "PROJ-9202-healthy", open_tasks=14, age_days=1)
    for _ in range(20):  # a full ladder's worth of failed execution attempts
        es.record(
            "PROJ-9201-churner", ok=False, reason="cannot run",
            artifacts=[], failures=["boom"], repo_root=tmp_path,
        )

    p0 = scheduler.pick_for_worker(0, 1, repo_root=tmp_path)
    assert p0 is not None and p0.id == "PROJ-9202-healthy", (
        "the churner (6 open) still outranked healthy work (14 open)"
    )
    # ...but it is not banished: with both workers it still gets served.
    picks = [scheduler.pick_for_worker(i, 2, repo_root=tmp_path) for i in range(2)]
    assert {p.id for p in picks if p} == {"PROJ-9201-churner", "PROJ-9202-healthy"}


def test_a_clean_project_is_not_penalised(tmp_path: Path) -> None:
    """A project that has never failed execution keeps pure shortest-remaining order."""
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    _impl_project(tmp_path, "PROJ-9301-near", open_tasks=2, age_days=1)
    _impl_project(tmp_path, "PROJ-9302-far", open_tasks=40, age_days=1)
    p0 = scheduler.pick_for_worker(0, 1, repo_root=tmp_path)
    assert p0 is not None and p0.id == "PROJ-9301-near"
