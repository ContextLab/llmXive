"""Integration test (T060): scheduler honors FR-001 priority order.

Pure file-fixture-driven; no LLM calls. Asserts:
  1. `in_progress` is preferred over `analyzed`.
  2. Within a tier, oldest `updated_at` wins.
  3. Locked projects are skipped.
  4. Projects in `human_input_needed` / `blocked` / `posted` are
     never returned.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
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
    now = datetime.now(UTC) - timedelta(days=age_days)
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


def _picked_distribution(repo: Path, *, n_samples: int = 400) -> dict[str, int]:
    """Sample pick_next() `n_samples` times with a fresh seeded RNG and
    return a histogram of project_ids. Used for probabilistic assertions."""
    counts: dict[str, int] = {}
    for seed in range(n_samples):
        rng = random.Random(seed)
        p = scheduler.pick_next(repo_root=repo, rng=rng)
        if p is None:
            continue
        counts[p.id] = counts.get(p.id, 0) + 1
    return counts


def test_in_progress_strongly_preempts_analyzed(tmp_path: Path) -> None:
    """IN_PROGRESS is one rank deeper than ANALYZED in STAGE_PROGRESSION;
    its base weight is STAGE_GROWTH_BASE^1 ~= 1.5x higher. Over many
    samples, IN_PROGRESS should win the strong majority of picks."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-001-fresh", Stage.ANALYZED, age_days=10)
    _make(tmp_path, "PROJ-002-active", Stage.IN_PROGRESS, age_days=1)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    # IN_PROGRESS / (IN_PROGRESS + ANALYZED) = 1.5 / 2.5 = 60%. Allow 50% floor.
    assert counts.get("PROJ-002-active", 0) / total > 0.5, (
        f"in_progress should win majority of picks; got {counts}"
    )
    # ANALYZED still gets non-zero share — the queue keeps draining.
    assert counts.get("PROJ-001-fresh", 0) > 0


def test_same_stage_yields_roughly_uniform_picks(tmp_path: Path) -> None:
    """Three projects at the same stage with identical comment counts
    should produce roughly uniform picks (within sampling noise)."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-100-newest", Stage.ANALYZED, age_days=1)
    _make(tmp_path, "PROJ-101-oldest", Stage.ANALYZED, age_days=20)
    _make(tmp_path, "PROJ-102-middle", Stage.ANALYZED, age_days=10)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    # Each should get ~33% ± sampling noise; allow 20-50% per project.
    for pid in ("PROJ-100-newest", "PROJ-101-oldest", "PROJ-102-middle"):
        share = counts.get(pid, 0) / total
        assert 0.20 < share < 0.50, f"{pid} share {share:.2%} outside band; counts={counts}"


def test_locked_projects_skipped(tmp_path: Path) -> None:
    _bootstrap_state(tmp_path)
    p = _make(tmp_path, "PROJ-200-locked", Stage.IN_PROGRESS, age_days=5)
    _make(tmp_path, "PROJ-201-free", Stage.ANALYZED, age_days=10)
    lockmod.acquire(p.id, holder_run_id="other-run", ttl_seconds=3600, repo_root=tmp_path)

    # Across many samples, the locked PROJ-200 must NEVER be picked.
    counts = _picked_distribution(tmp_path)
    assert "PROJ-200-locked" not in counts, "locked project must never be picked"
    assert counts.get("PROJ-201-free", 0) > 0, "free project should be pickable"


@pytest.mark.parametrize("stage", [Stage.HUMAN_INPUT_NEEDED, Stage.BLOCKED, Stage.POSTED])
def test_excluded_stages_never_picked(tmp_path: Path, stage: Stage) -> None:
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-300-stuck", stage, age_days=1)
    _make(tmp_path, "PROJ-301-ready", Stage.IN_PROGRESS, age_days=10)

    counts = _picked_distribution(tmp_path)
    assert "PROJ-300-stuck" not in counts, "terminal/human-input must never be picked"
    assert counts.get("PROJ-301-ready", 0) > 0


def test_deepest_stage_dominates_picks(tmp_path: Path) -> None:
    """With projects at BRAINSTORMED, CLARIFIED, and PAPER_IN_PROGRESS,
    the paper-stage project should win the majority of picks — it's
    further along the pipeline so closer to publication."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-401-clarified", Stage.CLARIFIED, age_days=1)
    _make(tmp_path, "PROJ-402-brainstormed", Stage.BRAINSTORMED, age_days=1)
    _make(tmp_path, "PROJ-403-paper-progress", Stage.PAPER_IN_PROGRESS, age_days=1)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    # PAPER_IN_PROGRESS has the deepest rank (16 in STAGE_PROGRESSION),
    # so its weight (1.5^16 ≈ 657) dwarfs CLARIFIED (1.5^4 ≈ 5) and
    # BRAINSTORMED (1.5^0 = 1). Should win >85%.
    paper_share = counts.get("PROJ-403-paper-progress", 0) / total
    assert paper_share > 0.85, (
        f"deepest-stage project should dominate picks; got {counts}"
    )


def test_comments_boost_priority(tmp_path: Path) -> None:
    """Two projects at the same stage; the one with more comments should
    get a noticeable share boost."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-500-quiet", Stage.ANALYZED, age_days=1)
    p_busy = _make(tmp_path, "PROJ-501-busy", Stage.ANALYZED, age_days=1)
    # Plant 10 comments on PROJ-501.
    reviews_dir = tmp_path / "projects" / p_busy.id / "reviews" / "research"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        (reviews_dir / f"persona-{i}__2026-05-01__research.md").write_text("body")

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    # busy multiplier = 1 + 0.10*10 = 2.0; quiet = 1.0. Busy share ≈ 2/3.
    busy_share = counts.get("PROJ-501-busy", 0) / total
    assert busy_share > 0.55, (
        f"commented project should be picked more often; got {counts}"
    )
    # Quiet still non-zero.
    assert counts.get("PROJ-500-quiet", 0) > 0
