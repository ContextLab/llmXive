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


def test_equal_depth_stages_split_evenly(tmp_path: Path) -> None:
    """At equal queue depth and equal staleness, two adjacent stages split
    picks ~evenly — `pick_next` selects a STAGE via `_stage_weights_with_floor`
    (the load-balancer that drives the population toward uniformity across
    columns), which is RANK-NEUTRAL, NOT the rank-capped `stage_weight`.

    Earlier revisions of this test asserted IN_PROGRESS "preempts" ANALYZED
    (old uncapped 1.5^rank model). The load-balanced scheduler superseded that:
    one project at ANALYZED and one at IN_PROGRESS each contribute the same
    `count - equal_share_target` over-target weight, so neither stage's depth
    buys it a majority. Derivation: total=2, base_target=2/21≈0.095, each
    over=1-0.095≈0.905 → exactly 0.50 each before sampling noise."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-001-fresh", Stage.ANALYZED, age_days=1)
    _make(tmp_path, "PROJ-002-active", Stage.IN_PROGRESS, age_days=1)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    # Expected 0.50/0.50; measured 0.477/0.522 over 400 seeded samples.
    # Band ±0.10 around 0.50 is robust to sampling noise yet still pins the
    # "neither stage's depth grants a majority" contract (rules out the old
    # >0.6 IN_PROGRESS dominance and a starved-ANALYZED outcome alike).
    in_progress_share = counts.get("PROJ-002-active", 0) / total
    assert 0.40 < in_progress_share < 0.60, (
        f"equal-depth/equal-staleness stages must split ~evenly; got {counts}"
    )
    # Neither queue is starved — both keep draining.
    assert counts.get("PROJ-001-fresh", 0) > 0
    assert counts.get("PROJ-002-active", 0) > 0


def test_stale_neglected_stage_gains_share(tmp_path: Path) -> None:
    """Spec 023 / FR-006: a queue NOT touched for two weeks out-weighs a
    fresh queue one rank deeper — neglect counterbalances rank."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-010-stale", Stage.ANALYZED, age_days=14)
    _make(tmp_path, "PROJ-011-fresh", Stage.IN_PROGRESS, age_days=0)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    assert counts.get("PROJ-010-stale", 0) / total > 0.4, (
        f"two-week-stale analyzed should claw back substantial share; {counts}"
    )


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


@pytest.mark.parametrize("stage", [Stage.BLOCKED, Stage.POSTED])
def test_excluded_stages_never_picked(tmp_path: Path, stage: Stage) -> None:
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-300-stuck", stage, age_days=1)
    _make(tmp_path, "PROJ-301-ready", Stage.IN_PROGRESS, age_days=10)

    counts = _picked_distribution(tmp_path)
    assert "PROJ-300-stuck" not in counts, "terminal stage must never be picked"
    assert counts.get("PROJ-301-ready", 0) > 0


def test_human_input_needed_is_auto_recovered(tmp_path: Path) -> None:
    """HUMAN_INPUT_NEEDED is a RETIRED parking stage (commit 404a05f43): it is
    deliberately NOT excluded, so a project stranded there IS eligible to be
    picked and auto-recovered (run_one_step routes it back to PLANNED). When
    it's the only runnable project it must appear in the picked distribution."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-310-stranded", Stage.HUMAN_INPUT_NEEDED, age_days=1)

    counts = _picked_distribution(tmp_path)
    assert counts.get("PROJ-310-stranded", 0) > 0, (
        f"stranded human_input_needed project must be pickable (auto-recovery); got {counts}"
    )


def test_equal_depth_stages_balance_not_dominate(tmp_path: Path) -> None:
    """With one project each at BRAINSTORMED, CLARIFIED, and PAPER_IN_PROGRESS
    (equal queue depth + equal staleness), the load-balanced `pick_next` gives
    all three a ROUGHLY-EQUAL share — pipeline depth does NOT grant the deepest
    stage dominance.

    Earlier revisions asserted PAPER_IN_PROGRESS "dominates" (>85%) under the
    old uncapped 1.5^rank model. `pick_next` now selects a stage via
    `_stage_weights_with_floor`, whose weight is `count - equal_share_target`
    (rank-NEUTRAL). Derivation: total=3, base_target=3/21≈0.143; CLARIFIED and
    PAPER_IN_PROGRESS over=1-0.143≈0.857, while BRAINSTORMED's target carries
    the +25% funnel-mouth headroom (0.143*1.25≈0.179) so its over≈0.821 is
    slightly lower → shares ≈ {clarified 0.338, paper 0.338, brainstormed
    0.324}. Measured 0.343/0.312/0.345 over 400 seeded samples."""
    _bootstrap_state(tmp_path)
    _make(tmp_path, "PROJ-401-clarified", Stage.CLARIFIED, age_days=1)
    _make(tmp_path, "PROJ-402-brainstormed", Stage.BRAINSTORMED, age_days=1)
    _make(tmp_path, "PROJ-403-paper-progress", Stage.PAPER_IN_PROGRESS, age_days=1)

    counts = _picked_distribution(tmp_path)
    total = sum(counts.values())
    shares = {pid: counts.get(pid, 0) / total for pid in (
        "PROJ-401-clarified", "PROJ-402-brainstormed", "PROJ-403-paper-progress")}
    # Each near 1/3; band [0.25, 0.42] is noise-robust yet still pins the
    # contract: the deepest stage does NOT dominate (rules out the old >0.85),
    # and every eligible stage clears the MIN_STAGE_SHARE=0.05 floor (none
    # starved). All three must clear the floor.
    for pid, share in shares.items():
        assert scheduler.MIN_STAGE_SHARE < share, (
            f"{pid} share {share:.2%} below MIN_STAGE_SHARE floor; counts={counts}"
        )
        assert 0.25 < share < 0.42, (
            f"{pid} share {share:.2%} outside balanced band; counts={counts}"
        )
    # The deepest stage must NOT dominate (the superseded behavior).
    assert shares["PROJ-403-paper-progress"] < 0.50, (
        f"deepest stage must not dominate under the load-balancer; got {counts}"
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
