"""Regression: scheduler fairness under a real-shaped population (FR-006).

Pre-023 the per-PROJECT exponential weighting gave the 589-deep
flesh_out_complete queue ~2% of picks while 92 paper-review projects
absorbed the rest (issue #303 funnel starvation). The two-level
stage-allocation roulette (bounded preference x depth x staleness, with
the MIN_STAGE_SHARE floor) must give every eligible stage a
non-vanishing share.

The synthetic population mirrors the real shape: hundreds early-stage,
dozens late-stage, a handful in between.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

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
    if stage in {Stage.PAPER_REVIEW, Stage.PAPER_COMPLETE}:
        kwargs["speckit_research_dir"] = f"projects/{project_id}/specs/001-t"
        kwargs["speckit_paper_dir"] = f"projects/{project_id}/paper/specs/001-p"
    if stage in {Stage.IN_PROGRESS, Stage.RESEARCH_COMPLETE}:
        kwargs["speckit_research_dir"] = f"projects/{project_id}/specs/001-t"
    if stage == Stage.HUMAN_INPUT_NEEDED:
        kwargs["human_escalation_reason"] = "fixture"
    p = Project(**kwargs)  # type: ignore[arg-type]
    project_store.save(p, repo_root=repo)
    return p


@pytest.fixture
def population(tmp_path: Path) -> Path:
    """Real-shaped population (scaled ~1/3 to keep the suite fast): many
    stale flesh_out_complete, dozens paper_review, a few in between."""
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    for i in range(80):
        _make(tmp_path, f"PROJ-{1000 + i}-idea", Stage.FLESH_OUT_COMPLETE, age_days=30)
    for i in range(15):
        _make(tmp_path, f"PROJ-{2000 + i}-paper", Stage.PAPER_REVIEW, age_days=2)
    for i in range(5):
        _make(tmp_path, f"PROJ-{3000 + i}-impl", Stage.IN_PROGRESS, age_days=5)
    for i in range(3):
        _make(tmp_path, f"PROJ-{4000 + i}-brain", Stage.BRAINSTORMED, age_days=10)
    _make(tmp_path, "PROJ-5000-human", Stage.HUMAN_INPUT_NEEDED, age_days=1)
    _make(tmp_path, "PROJ-5001-posted", Stage.POSTED, age_days=1)
    return tmp_path


def _stage_shares(repo: Path, *, n_samples: int = 300) -> dict[Stage, float]:
    counts: dict[Stage, int] = {}
    for seed in range(n_samples):
        p = scheduler.pick_next(repo_root=repo, rng=random.Random(seed))
        assert p is not None
        counts[p.current_stage] = counts.get(p.current_stage, 0) + 1
    return {s: c / n_samples for s, c in counts.items()}


def test_every_eligible_stage_gets_a_nonvanishing_share(population: Path) -> None:
    shares = _stage_shares(population)
    # The MIN_STAGE_SHARE floor (5%) minus sampling noise.
    for stage in (
        Stage.FLESH_OUT_COMPLETE,
        Stage.PAPER_REVIEW,
        Stage.IN_PROGRESS,
        Stage.BRAINSTORMED,
    ):
        assert shares.get(stage, 0.0) > 0.03, (
            f"{stage.value} share {shares.get(stage, 0.0):.1%} is vanishing "
            f"(FR-006); shares={ {s.value: f'{v:.1%}' for s, v in shares.items()} }"
        )


def test_load_balancing_drains_the_overfull_stage(population: Path) -> None:
    """Load-balancing policy (replaces the old late-stage 'finish-what-is-
    started' bias): the most OVER-target stage — the 80-deep flesh_out_complete
    queue — gets the dominant share so it drains toward the equal-per-stage
    target, while every UNDER-target stage (paper_review, in_progress,
    brainstormed) just coasts at the MIN_STAGE_SHARE floor."""
    shares = _stage_shares(population)
    foc = shares.get(Stage.FLESH_OUT_COMPLETE, 0.0)
    assert foc > 0.6, shares  # the overfull stage is drained the most
    for s in (Stage.PAPER_REVIEW, Stage.IN_PROGRESS, Stage.BRAINSTORMED):
        assert shares.get(s, 0.0) < foc  # under-target stages coast at the floor


def test_never_pick_stages_stay_excluded(population: Path) -> None:
    for seed in range(300):
        p = scheduler.pick_next(repo_root=population, rng=random.Random(seed))
        assert p is not None
        assert p.current_stage not in scheduler._NEVER_PICK


def test_stage_restricted_pick_unchanged(population: Path) -> None:
    """`--stage` lanes pick within the requested stage only."""
    for seed in range(50):
        p = scheduler.pick_next(
            repo_root=population,
            stage=Stage.FLESH_OUT_COMPLETE,
            rng=random.Random(seed),
        )
        assert p is not None
        assert p.current_stage == Stage.FLESH_OUT_COMPLETE


def test_balancer_weights_overflow_with_brainstorm_headroom() -> None:
    """`_stage_weights_with_floor` weights each stage by how far its queue
    exceeds the equal-share target, and `brainstormed` carries +25% headroom
    before the balancer starts draining it."""
    from llmxive.pipeline.scheduler import (
        BRAINSTORM_HEADROOM,
        _stage_weights_with_floor,
    )

    assert BRAINSTORM_HEADROOM == 1.25
    now = datetime.now(UTC)

    counter = [8000]

    def projs(stage: Stage, n: int) -> list[Project]:
        out = []
        for _ in range(n):
            counter[0] += 1
            out.append(Project(
                id=f"PROJ-{counter[0]}-w", title="t", field="t",
                current_stage=stage, created_at=now, updated_at=now,
                artifact_hashes={},
            ))
        return out

    # base target is now the FULL-pipeline uniform share: total / max(occupied,
    # len(STAGE_PROGRESSION)) = 210 / max(3, 20) = 210/20 = 10.5 (NOT 210/3=70 —
    # the target is "uniform across all columns", so it doesn't float up when only
    # a few stages are occupied). validated & brainstormed both 100 (far over base);
    # flesh_out_complete 10 (still under 10.5 → floor only). brainstorm target
    # 10.5*1.25=13.125, validated's 10.5 → brainstormed drains slightly less.
    by_stage = {
        Stage.VALIDATED: projs(Stage.VALIDATED, 100),
        Stage.BRAINSTORMED: projs(Stage.BRAINSTORMED, 100),
        Stage.FLESH_OUT_COMPLETE: projs(Stage.FLESH_OUT_COMPLETE, 10),
    }
    w = _stage_weights_with_floor(by_stage)
    assert w[Stage.VALIDATED] > w[Stage.FLESH_OUT_COMPLETE]  # over-target drains first
    assert w[Stage.VALIDATED] > w[Stage.BRAINSTORMED]   # +25% headroom -> drained less
    assert w[Stage.FLESH_OUT_COMPLETE] > 0              # floor keeps it pickable


def test_full_pipeline_uniform_target_drains_a_lumpy_pile() -> None:
    """Spec: load-balance toward UNIFORMITY across ALL pipeline columns.

    The equal-share target is the full-pipeline uniform share
    ``total / max(occupied, len(STAGE_PROGRESSION))`` — NOT ``total / occupied``,
    which would float upward (and under-drain giant piles) when only a few
    columns are populated. With a lumpy distribution we assert:
      (a) the giant pile (200) receives the DOMINANT share of the weight, and
      (b) a stage whose count is over the full-pipeline target has positive
          overflow and a final weight strictly ABOVE the MIN_STAGE_SHARE floor,
          while a stage well below the target gets ONLY the floor.
    """
    from llmxive.pipeline.scheduler import (
        MIN_STAGE_SHARE,
        STAGE_PROGRESSION,
        _stage_target,
        _stage_weights_with_floor,
    )

    now = datetime.now(UTC)
    counter = [9000]

    def projs(stage: Stage, n: int) -> list[Project]:
        out = []
        for _ in range(n):
            counter[0] += 1
            out.append(Project(
                id=f"PROJ-{counter[0]}-w", title="t", field="t",
                current_stage=stage, created_at=now, updated_at=now,
                artifact_hashes={},
            ))
        return out

    # Lumpy: one 200-deep pile, one mid stage over target, two tiny stages.
    # Stages chosen so Project validation needs no speckit dirs. total = 243.
    # full-pipeline target = total / max(occupied, len(STAGE_PROGRESSION)); the
    # OCCUPIED-only target would be 243/4 = 60.75 and the 40-deep stage would NOT
    # count as over-target (the bug this fix corrects). Derived from the LIVE
    # progression length so adding a pipeline column can't silently break it.
    counts = {
        Stage.PROJECT_INITIALIZED: 200,   # the giant pile
        Stage.FLESH_OUT_IN_PROGRESS: 40,  # over the full-pipeline target
        Stage.VALIDATED: 1,               # well below target -> floor only
        Stage.FLESH_OUT_COMPLETE: 2,      # well below target -> floor only
    }
    by_stage = {s: projs(s, n) for s, n in counts.items()}
    total = sum(counts.values())
    target = total / max(len(by_stage), len(STAGE_PROGRESSION))
    # Few columns occupied -> the denominator is the FULL pipeline width, so the
    # target is the full-pipeline share (well below the occupied-only 243/4).
    assert len(by_stage) < len(STAGE_PROGRESSION)
    assert target == pytest.approx(total / len(STAGE_PROGRESSION))
    assert target < total / len(by_stage)

    over = {s: max(0.0, counts[s] - _stage_target(s, target)) for s in by_stage}
    floor = MIN_STAGE_SHARE * sum(over.values())
    w = _stage_weights_with_floor(by_stage)

    # (a) the 200-pile dominates the pick weight.
    pile_share = w[Stage.PROJECT_INITIALIZED] / sum(w.values())
    assert pile_share > 0.6, w

    # (b) the over-target mid stage has positive overflow AND a weight above the
    # floor; the well-below stages have zero overflow and sit exactly at the floor.
    assert over[Stage.FLESH_OUT_IN_PROGRESS] > 0
    assert w[Stage.FLESH_OUT_IN_PROGRESS] > floor
    assert over[Stage.VALIDATED] == 0.0
    assert over[Stage.FLESH_OUT_COMPLETE] == 0.0
    assert w[Stage.VALIDATED] == pytest.approx(floor)
    assert w[Stage.FLESH_OUT_COMPLETE] == pytest.approx(floor)
