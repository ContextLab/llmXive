"""Integration test for research-review verdict routing
(spec 015 T042 / FR-034).

The transient RESEARCH_MINOR_REVISION stage was deleted. Any
non-convergence at RESEARCH_REVIEW now routes through the convergence
engine's adapter: the project STAYS at RESEARCH_REVIEW with a new
``revision_spec_path`` pointing at the round dir the adapter wrote.
Unanimous accept → RESEARCH_ACCEPTED; full_revision → RESEARCH_FULL_REVISION
(kept); reject → RESEARCH_REJECTED (kept).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents import advancement
from llmxive.state import citations as citations_store
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    ActionItem,
    BackendName,
    Citation,
    CitationKind,
    Project,
    ReviewerKind,
    ReviewRecord,
    Stage,
    VerificationStatus,
)

PROJ_ID = "PROJ-001-review"


def _bootstrap(repo: Path) -> Project:
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)
    feature_dir = repo / "projects" / PROJ_ID / "specs" / "001-review"
    feature_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = feature_dir / "tasks.md"
    tasks_path.write_text("- [X] T001 done\n", encoding="utf-8")

    now = datetime.now(UTC)
    p = Project(
        id=PROJ_ID,
        title="review test",
        field="test",
        current_stage=Stage.RESEARCH_REVIEW,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={
            f"projects/{PROJ_ID}/specs/001-review/tasks.md": project_store.hash_file(tasks_path)
        },
        speckit_research_dir=f"projects/{PROJ_ID}/specs/001-review",
    )
    project_store.save(p, repo_root=repo)
    return p


def _make_record(
    repo: Path,
    project: Project,
    *,
    reviewer_name: str,
    verdict: str,
    action_items: list[ActionItem] | None = None,
) -> ReviewRecord:
    score = 0.5 if verdict == "accept" else 0.0
    artifact_path = next(iter(project.artifact_hashes))
    rec_kwargs: dict = dict(
        reviewer_name=reviewer_name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=artifact_path,
        artifact_hash=project.artifact_hashes[artifact_path],
        score=score,
        verdict=verdict,
        feedback=f"{verdict} from {reviewer_name}",
        reviewed_at=datetime.now(UTC),
        prompt_version="1.0.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
    )
    if action_items is not None and verdict != "accept":
        rec_kwargs["prompt_version"] = "1.1.0"
        rec_kwargs["action_items"] = action_items
    rec = ReviewRecord(**rec_kwargs)
    reviews_store.write(
        rec,
        body=f"Recommendation: {verdict}",
        stage="research",
        review_type="research",
        produced_by_agent=None,
        repo_root=repo,
    )
    return rec


def test_unanimous_accept_advances_to_research_accepted(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    for i in range(3):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_ACCEPTED, (
        f"expected research_accepted; got {out.current_stage.value}"
    )


def test_minor_revision_routes_through_engine_adapter(tmp_path: Path) -> None:
    """Spec 015 T042: a winning `minor_revision` no longer transitions
    to a transient stage; instead the engine adapter writes a round dir
    and the project STAYS at RESEARCH_REVIEW with revision_spec_path."""
    project = _bootstrap(tmp_path)
    _make_record(
        tmp_path, project, reviewer_name="rev_a", verdict="minor_revision",
        action_items=[ActionItem.from_text("Re-task analysis.py.", "writing")],
    )
    _make_record(
        tmp_path, project, reviewer_name="rev_b", verdict="minor_revision",
        action_items=[ActionItem.from_text("Re-task analysis.py.", "writing")],
    )

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_REVIEW
    assert out.revision_spec_path is not None
    assert "auto-revisions" in out.revision_spec_path
    spec_dir = tmp_path / out.revision_spec_path
    assert (spec_dir / "tasks.md").is_file()


def test_full_revision_winning(tmp_path: Path) -> None:
    """RESEARCH_FULL_REVISION is retained for prompt_version 1.0.x
    records without action_items (legacy back-compat)."""
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="full_revision")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_FULL_REVISION


def test_reject_winning(tmp_path: Path) -> None:
    """RESEARCH_REJECTED is retained for fatal judgments (legacy 1.0.x)."""
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="reject")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_REJECTED


def test_citation_blocks_accept(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    for i in range(3):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    artifact_path = next(iter(project.artifact_hashes))
    bad = Citation(
        cite_id="fake-001",
        artifact_path=artifact_path,
        artifact_hash=project.artifact_hashes[artifact_path],
        kind=CitationKind.URL,
        value="https://example.invalid/fake",
        cited_title="Fake Paper",
        verification_status=VerificationStatus.MISMATCH,
        fetched_title="Wholly Unrelated Page",
        verified_at=datetime.now(UTC),
    )
    citations_store.save(project.id, [bad], repo_root=tmp_path)

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage != Stage.RESEARCH_ACCEPTED, (
        "fabricated citation must block research_accepted"
    )
