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


def test_late_stage_preference_is_kept_but_bounded(population: Path) -> None:
    """Late stages still lead (finish-what-is-started), but no longer
    absorb effectively everything: the deep, stale idea queue's share must
    be meaningfully ABOVE its floor, and paper_review must be below 90%."""
    shares = _stage_shares(population)
    assert shares.get(Stage.PAPER_REVIEW, 0.0) > shares.get(Stage.BRAINSTORMED, 0.0)
    assert shares.get(Stage.PAPER_REVIEW, 0.0) < 0.90
    assert shares.get(Stage.FLESH_OUT_COMPLETE, 0.0) > 0.03


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


def test_stage_weight_counterweights() -> None:
    """Depth and staleness both increase a stage's weight; the rank
    preference is capped at STAGE_RANK_CAP."""
    now = datetime.now(UTC)

    def proj(i: int, stage: Stage, days: float) -> Project:
        pid = f"PROJ-{7000 + i}-w"
        return Project(
            id=pid,
            title="w",
            field="test",
            current_stage=stage,
            created_at=now - timedelta(days=days),
            updated_at=now - timedelta(days=days),
            artifact_hashes={},
            speckit_research_dir=f"projects/{pid}/specs/001-t",
            speckit_paper_dir=f"projects/{pid}/paper/specs/001-p",
        )

    shallow = [proj(0, Stage.FLESH_OUT_COMPLETE, 1.0)]
    deep = [proj(i, Stage.FLESH_OUT_COMPLETE, 1.0) for i in range(100)]
    assert scheduler.stage_weight(
        Stage.FLESH_OUT_COMPLETE, deep, now=now
    ) > scheduler.stage_weight(Stage.FLESH_OUT_COMPLETE, shallow, now=now)

    fresh = [proj(0, Stage.FLESH_OUT_COMPLETE, 0.1)]
    stale = [proj(1, Stage.FLESH_OUT_COMPLETE, 30.0)]
    assert scheduler.stage_weight(
        Stage.FLESH_OUT_COMPLETE, stale, now=now
    ) > scheduler.stage_weight(Stage.FLESH_OUT_COMPLETE, fresh, now=now)

    # Rank preference saturates at the cap: PAPER_REVIEW (rank 18) and the
    # capped rank stage weigh the same per-queue, all else equal.
    capped_stage = scheduler.STAGE_PROGRESSION[scheduler.STAGE_RANK_CAP]
    a = [proj(0, Stage.PAPER_REVIEW, 1.0)]
    b = [proj(1, capped_stage, 1.0)]
    assert scheduler.stage_weight(Stage.PAPER_REVIEW, a, now=now) == pytest.approx(
        scheduler.stage_weight(capped_stage, b, now=now)
    )
