"""Regression: per-project locking holds across concurrent lanes
(spec 023 / FR-007 + concurrent-lanes edge case).

Two scheduled lanes (or a lane and a manual dispatch) may target the same
project. The discipline: the scheduler never picks an actively-locked
project; a pass that loses the pick→lock race aborts with ``LockError``
BEFORE mutating any state (the loser retries on a later tick); a stale
lock is reclaimed.

The review-stage evaluation path is the sharpest case: with a complete
current verdict set there is NO agent dispatch (FR-004), so the lock must
be taken explicitly around evaluate+save — otherwise two lanes could both
evaluate and race on the auto-revisions round dir.
"""

from __future__ import annotations

import random
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.agents import advancement
from llmxive.pipeline import graph, scheduler
from llmxive.pipeline import lock as lockmod
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    ActionItem,
    BackendName,
    Project,
    ReviewerKind,
    ReviewRecord,
    Stage,
)

REAL_REPO = Path(__file__).resolve().parents[2]
PROJ_ID = "PROJ-907-locking"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "agents").mkdir()
    shutil.copy(
        REAL_REPO / "agents" / "registry.yaml",
        tmp_path / "agents" / "registry.yaml",
    )
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _bootstrap(repo: Path) -> tuple[Project, str]:
    feature = repo / "projects" / PROJ_ID / "paper" / "specs" / "001-paper"
    feature.mkdir(parents=True, exist_ok=True)
    tasks_path = feature / "tasks.md"
    tasks_path.write_text("- [X] T001 done\n", encoding="utf-8")
    live_hash = project_store.hash_file(tasks_path)
    now = datetime.now(UTC)
    project = Project(
        id=PROJ_ID,
        title="locking test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        created_at=now,
        updated_at=now,
        artifact_hashes={str(tasks_path.relative_to(repo)): live_hash},
    )
    project_store.save(project, repo_root=repo)
    for name in advancement._required_specialists("paper_reviewer_", repo_root=repo):
        rec = ReviewRecord(
            reviewer_name=name,
            reviewer_kind=ReviewerKind.LLM,
            artifact_path=str(tasks_path.relative_to(repo)),
            artifact_hash=live_hash,
            score=0.0,
            verdict="minor_revision",
            feedback="x",
            reviewed_at=now,
            prompt_version="1.1.0",
            model_name="qwen.qwen3.5-122b",
            backend=BackendName.DARTMOUTH,
            action_items=[ActionItem.from_text("Tighten section 1.", "writing")],
        )
        reviews_store.write(
            rec, body="x", stage="paper", review_type="paper",
            produced_by_agent=None, repo_root=repo,
        )
    return project, live_hash


def test_scheduler_never_picks_a_locked_project(repo: Path) -> None:
    project, _ = _bootstrap(repo)
    lockmod.acquire(
        project.id, holder_run_id="lane-A", ttl_seconds=3600, repo_root=repo
    )
    for seed in range(100):
        picked = scheduler.pick_next(repo_root=repo, rng=random.Random(seed))
        assert picked is None, "the only project is locked — nothing to pick"


def test_losing_lane_aborts_before_any_state_mutation(repo: Path) -> None:
    """Lane A holds the lock; lane B's run_one_step on the same project
    must raise LockError WITHOUT writing a revision round or touching the
    saved project state."""
    project, _ = _bootstrap(repo)
    lockmod.acquire(
        project.id, holder_run_id="lane-A", ttl_seconds=3600, repo_root=repo
    )
    before = project_store.load(PROJ_ID, repo_root=repo)

    with pytest.raises(lockmod.LockError):
        graph.run_one_step(project, repo_root=repo, run_id="lane-B")

    after = project_store.load(PROJ_ID, repo_root=repo)
    assert after.revision_spec_path is None
    assert after.updated_at == before.updated_at
    assert not (repo / "specs" / "auto-revisions" / PROJ_ID).exists(), (
        "the losing lane must not have written a revision round"
    )


def test_loser_succeeds_on_retry_after_release(repo: Path) -> None:
    project, _ = _bootstrap(repo)
    lockmod.acquire(
        project.id, holder_run_id="lane-A", ttl_seconds=3600, repo_root=repo
    )
    with pytest.raises(lockmod.LockError):
        graph.run_one_step(project, repo_root=repo, run_id="lane-B")
    lockmod.release(project.id, holder_run_id="lane-A", repo_root=repo)

    out = graph.run_one_step(project, repo_root=repo, run_id="lane-B-retry")

    assert out.revision_spec_path, "retry after release completes the evaluation"
    assert not lockmod.is_locked(project.id, repo_root=repo), (
        "the lock is released after the pass"
    )


def test_stale_lock_is_reclaimed(repo: Path) -> None:
    project, _ = _bootstrap(repo)
    # Write an EXPIRED lock file directly (acquire() refuses to create
    # one whose expiry precedes its acquisition).
    import yaml

    past = datetime(2020, 1, 1, tzinfo=UTC)
    lock_path = repo / "state" / "locks" / f"{project.id}.lock"
    lock_path.write_text(
        yaml.safe_dump(
            {
                "project_id": project.id,
                "holder_run_id": "lane-dead",
                "acquired_at": past.isoformat(),
                "expires_at": datetime(2020, 1, 1, 1, tzinfo=UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    out = graph.run_one_step(project, repo_root=repo, run_id="lane-B")

    assert out.revision_spec_path, "expired locks must not block progress"
