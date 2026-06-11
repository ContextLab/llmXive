"""Regression: review-stage advancement decisions are PERSISTED (spec 023 US1).

The issue-#303 root cause: ``_decide_next_stage`` ran
``advancement.evaluate`` and returned only ``evaluated.current_stage`` —
the revision work-spec reference (``revision_spec_path``), kickback
provenance, and even the accept decision were computed every tick and then
discarded before save. 92 papers looped at review forever; zero papers
were ever accepted.

These tests drive the REAL ``graph.run_one_step`` over a synthetic repo
(real registry copy, real review-record files, real project state on
disk). Only the agent-execution boundary (``graph.run_agent``) is replaced
with a recording no-op — reviewer/implementer execution is exercised by
the real-call suites (T009), not here.

Covers BOTH tracks (FR-001), same-pass accept advancement (FR-005), and
the bounded revision-round cap → honest terminal (spec 023 edge case).
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


@pytest.fixture
def dispatched() -> list[str]:
    return []


@pytest.fixture
def repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dispatched: list[str]
) -> Path:
    """Synthetic repo with the REAL agent registry (so the required
    specialist sets are the production ones) and a recording no-op at the
    agent-execution boundary."""
    (tmp_path / "agents").mkdir()
    shutil.copy(REAL_REPO / "agents" / "registry.yaml", tmp_path / "agents" / "registry.yaml")
    for sub in ("projects", "run-log", "locks", "citations"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)

    def _record_dispatch(agent, ctx, *, repo_root=None):
        dispatched.append(agent.entry.name)

    monkeypatch.setattr(graph, "run_agent", _record_dispatch)
    return tmp_path


def _bootstrap(repo: Path, *, track: str, project_id: str) -> tuple[Project, str]:
    """Project at the track's review stage with a live tasks.md artifact."""
    if track == "paper":
        feature = repo / "projects" / project_id / "paper" / "specs" / "001-paper"
        stage = Stage.PAPER_REVIEW
    else:
        feature = repo / "projects" / project_id / "specs" / "001-research"
        stage = Stage.RESEARCH_REVIEW
    feature.mkdir(parents=True, exist_ok=True)
    tasks_path = feature / "tasks.md"
    tasks_path.write_text("- [X] T001 done\n", encoding="utf-8")
    live_hash = project_store.hash_file(tasks_path)
    now = datetime.now(UTC)
    project = Project(
        id=project_id,
        title=f"{track} persistence test",
        field="test",
        current_stage=stage,
        created_at=now,
        updated_at=now,
        artifact_hashes={str(tasks_path.relative_to(repo)): live_hash},
    )
    project_store.save(project, repo_root=repo)
    return project, live_hash


def _write_record(
    repo: Path,
    project: Project,
    *,
    reviewer_name: str,
    verdict: str,
    track: str,
    artifact_hash: str,
    items: list[ActionItem] | None = None,
) -> None:
    rec = ReviewRecord(
        reviewer_name=reviewer_name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=next(iter(project.artifact_hashes)),
        artifact_hash=artifact_hash,
        score=0.5 if verdict == "accept" else 0.0,
        verdict=verdict,
        feedback=f"{verdict} from {reviewer_name}",
        reviewed_at=datetime.now(UTC),
        prompt_version="1.1.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=items or [],
    )
    reviews_store.write(
        rec,
        body=f"Recommendation: {verdict}",
        stage=track,
        review_type=track,
        produced_by_agent=None,
        repo_root=repo,
    )


def _required(repo: Path, track: str) -> set[str]:
    prefix = "paper_reviewer_" if track == "paper" else "research_reviewer_"
    names = advancement._required_specialists(prefix, repo_root=repo)
    assert names, f"real registry must define {prefix}* specialists"
    return names


REVISE_ITEM = [ActionItem.from_text("Fix the typo in section 2.", "writing")]


@pytest.mark.parametrize("track,project_id", [
    ("paper", "PROJ-901-persist-paper"),
    ("research", "PROJ-902-persist-research"),
])
def test_revision_decision_is_persisted_both_tracks(
    repo: Path, dispatched: list[str], track: str, project_id: str
) -> None:
    """FR-001: a complete current verdict set demanding revision leaves the
    SAVED project state carrying revision_spec_path, with the work-spec on
    disk — on both graph shapes (research and paper)."""
    project, live_hash = _bootstrap(repo, track=track, project_id=project_id)
    for name in _required(repo, track):
        _write_record(
            repo, project, reviewer_name=name, verdict="minor_revision",
            track=track, artifact_hash=live_hash, items=REVISE_ITEM,
        )

    out = graph.run_one_step(project, repo_root=repo)

    saved = project_store.load(project_id, repo_root=repo)
    assert saved.revision_spec_path, (
        "the revise decision must survive the pass in SAVED state "
        "(the discarded-decision bug)"
    )
    assert saved.revision_spec_path == out.revision_spec_path
    assert "auto-revisions" in saved.revision_spec_path
    assert (repo / saved.revision_spec_path / "tasks.md").is_file(), (
        "the revision work-spec body must exist on disk"
    )
    review_stage = Stage.PAPER_REVIEW if track == "paper" else Stage.RESEARCH_REVIEW
    assert saved.current_stage == review_stage
    # Complete + current verdicts → NO reviewer was re-dispatched (FR-004).
    assert dispatched == []


def test_all_accept_advances_same_pass(repo: Path, dispatched: list[str]) -> None:
    """FR-005: every required specialist's current verdict is accept → the
    project advances out of review IN THE SAME PASS, persisted."""
    project, live_hash = _bootstrap(
        repo, track="paper", project_id="PROJ-903-accept"
    )
    for name in _required(repo, "paper"):
        _write_record(
            repo, project, reviewer_name=name, verdict="accept",
            track="paper", artifact_hash=live_hash,
        )

    out = graph.run_one_step(project, repo_root=repo)

    assert out.current_stage == Stage.PAPER_ACCEPTED
    saved = project_store.load("PROJ-903-accept", repo_root=repo)
    assert saved.current_stage == Stage.PAPER_ACCEPTED
    assert dispatched == []


def test_revision_cap_routes_to_honest_terminal(repo: Path) -> None:
    """Spec 023 edge case: after MAX_REVISION_ROUNDS rounds without
    convergence, the next revise decision takes the honest terminal
    (PAPER_FUNDAMENTAL_FLAWS), never a silent round-N+1 loop."""
    project, live_hash = _bootstrap(
        repo, track="paper", project_id="PROJ-904-cap"
    )
    for n in range(1, advancement.MAX_REVISION_ROUNDS + 1):
        (repo / "specs" / "auto-revisions" / project.id / f"round-{n}").mkdir(
            parents=True
        )
    for name in _required(repo, "paper"):
        _write_record(
            repo, project, reviewer_name=name, verdict="minor_revision",
            track="paper", artifact_hash=live_hash, items=REVISE_ITEM,
        )

    out = graph.run_one_step(project, repo_root=repo)

    assert out.current_stage == Stage.PAPER_FUNDAMENTAL_FLAWS
    saved = project_store.load(project.id, repo_root=repo)
    assert saved.current_stage == Stage.PAPER_FUNDAMENTAL_FLAWS
    assert not saved.revision_spec_path
    # No round-4 was written.
    assert not (
        repo / "specs" / "auto-revisions" / project.id
        / f"round-{advancement.MAX_REVISION_ROUNDS + 1}"
    ).exists()
