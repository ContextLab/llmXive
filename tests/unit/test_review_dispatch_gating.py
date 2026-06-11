"""Regression: reviewer fan-out is gated by verdict coverage (spec 023 US1).

Pre-023 behavior: EVERY scheduled pick of a review-stage project
re-dispatched the full reviewer panel against the unchanged artifact —
~83% of all agent runs were these no-op re-reviews (issue #303).

After FR-004: a complete current verdict set → zero reviewer dispatches;
a stale set → only the stale specialists; an incomplete set → only the
missing specialists; an unconsumed revision work-spec → the revision
implementer, never reviewers (FR-002).

Same harness as test_graph_advancement_persistence: real registry, real
records on disk, recording no-op at the ``graph.run_agent`` boundary.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.agents import advancement
from llmxive.pipeline import graph
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
PROJ_ID = "PROJ-905-gating"


@pytest.fixture
def dispatched() -> list[str]:
    return []


@pytest.fixture
def repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatched: list[str]
) -> Path:
    (tmp_path / "agents").mkdir()
    shutil.copy(
        REAL_REPO / "agents" / "registry.yaml",
        tmp_path / "agents" / "registry.yaml",
    )
    for sub in ("projects", "run-log", "locks", "citations"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)

    def _record_dispatch(agent, ctx, *, repo_root=None):
        dispatched.append(agent.entry.name)

    monkeypatch.setattr(graph, "run_agent", _record_dispatch)
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
        title="gating test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        created_at=now,
        updated_at=now,
        artifact_hashes={str(tasks_path.relative_to(repo)): live_hash},
    )
    project_store.save(project, repo_root=repo)
    return project, live_hash


def _write_record(
    repo: Path, *, reviewer_name: str, artifact_hash: str, verdict: str = "accept"
) -> None:
    items = (
        [] if verdict == "accept"
        else [ActionItem.from_text("Tighten the abstract.", "writing")]
    )
    rec = ReviewRecord(
        reviewer_name=reviewer_name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=f"projects/{PROJ_ID}/paper/specs/001-paper/tasks.md",
        artifact_hash=artifact_hash,
        score=0.5 if verdict == "accept" else 0.0,
        verdict=verdict,
        feedback="x",
        reviewed_at=datetime.now(UTC),
        prompt_version="1.1.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=items,
    )
    reviews_store.write(
        rec, body="x", stage="paper", review_type="paper",
        produced_by_agent=None, repo_root=repo,
    )


def _required(repo: Path) -> list[str]:
    names = sorted(
        advancement._required_specialists("paper_reviewer_", repo_root=repo)
    )
    assert len(names) >= 2, "gating tests need >=2 required specialists"
    return names


def test_complete_current_set_dispatches_nothing(
    repo: Path, dispatched: list[str]
) -> None:
    project, live_hash = _bootstrap(repo)
    for name in _required(repo):
        _write_record(repo, reviewer_name=name, artifact_hash=live_hash)

    graph.run_one_step(project, repo_root=repo)

    assert dispatched == [], (
        "complete current verdict set must trigger ZERO reviewer calls "
        "(FR-004 — the 83%%-no-op-re-review bug)"
    )


def test_stale_specialist_is_the_only_redispatch(
    repo: Path, dispatched: list[str]
) -> None:
    """The stale-verdict edge case: the artifact changed after one
    specialist reviewed — only that specialist is re-dispatched."""
    project, live_hash = _bootstrap(repo)
    names = _required(repo)
    stale_name, current_names = names[0], names[1:]
    _write_record(repo, reviewer_name=stale_name, artifact_hash="0" * 64)
    for name in current_names:
        _write_record(repo, reviewer_name=name, artifact_hash=live_hash)

    graph.run_one_step(project, repo_root=repo)

    assert dispatched == [stale_name], (
        f"only the stale specialist should re-run; got {dispatched}"
    )


def test_missing_specialists_are_the_only_dispatch(
    repo: Path, dispatched: list[str]
) -> None:
    """An incomplete set: one specialist never reviewed — only that
    specialist is dispatched (the generic reviewer is not re-run because
    records already exist)."""
    project, live_hash = _bootstrap(repo)
    names = _required(repo)
    missing_name, present_names = names[0], names[1:]
    for name in present_names:
        _write_record(repo, reviewer_name=name, artifact_hash=live_hash)

    graph.run_one_step(project, repo_root=repo)

    assert dispatched == [missing_name], (
        f"only the missing specialist should run; got {dispatched}"
    )


def test_first_round_dispatches_generic_plus_all_specialists(
    repo: Path, dispatched: list[str]
) -> None:
    """A project with NO records at all gets the full first-round panel:
    every required specialist plus the generic reviewer."""
    project, _ = _bootstrap(repo)

    graph.run_one_step(project, repo_root=repo)

    expected = set(_required(repo)) | {"paper_reviewer"}
    assert set(dispatched) == expected


def test_unconsumed_workspec_dispatches_implementer_not_reviewers(
    repo: Path, dispatched: list[str]
) -> None:
    """FR-002: a saved unconsumed revision work-spec routes the pick to the
    revision implementer — reviewers are NOT re-dispatched."""
    project, live_hash = _bootstrap(repo)
    spec_dir = repo / "specs" / "auto-revisions" / PROJ_ID / "round-1"
    spec_dir.mkdir(parents=True)
    (spec_dir / "tasks.md").write_text("- [ ] R1 fix\n", encoding="utf-8")
    project = project.model_copy(
        update={"revision_spec_path": str(spec_dir.relative_to(repo))}
    )
    project_store.save(project, repo_root=repo)
    for name in _required(repo):
        _write_record(
            repo, reviewer_name=name, artifact_hash=live_hash,
            verdict="minor_revision",
        )

    graph.run_one_step(project, repo_root=repo)

    assert dispatched == ["llmxive_implementer"], (
        f"work-spec must route to the revision implementer, got {dispatched}"
    )
