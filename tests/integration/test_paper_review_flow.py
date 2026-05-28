"""Integration test for paper-review verdict routing
(spec 015 T042 / FR-034).

The 7 transient paper-revision stages were deleted. Any non-convergence
at PAPER_REVIEW now routes through the convergence engine's adapter:
the project STAYS at PAPER_REVIEW with a new
``revision_spec_path`` pointing at the round dir the adapter wrote.
Unanimous accept → PAPER_ACCEPTED; FATAL judgments → BRAINSTORMED.
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

PROJ_ID = "PROJ-001-paperreview"


def _bootstrap(repo: Path) -> Project:
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)
    paper_feature = repo / "projects" / PROJ_ID / "paper" / "specs" / "001-paper"
    paper_feature.mkdir(parents=True, exist_ok=True)
    tasks_path = paper_feature / "tasks.md"
    tasks_path.write_text("- [X] T001 done\n", encoding="utf-8")

    now = datetime.now(UTC)
    p = Project(
        id=PROJ_ID,
        title="paper review test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        points_research={"research_review": 5.0},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={
            f"projects/{PROJ_ID}/paper/specs/001-paper/tasks.md": project_store.hash_file(tasks_path)
        },
        speckit_research_dir=f"projects/{PROJ_ID}/specs/001-research",
        speckit_paper_dir=f"projects/{PROJ_ID}/paper/specs/001-paper",
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
        stage="paper",
        review_type="paper",
        produced_by_agent=None,
        repo_root=repo,
    )
    return rec


def test_unanimous_accept_advances_to_paper_accepted(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    # Spec 015: unanimous LLM-panel acceptance is the sole gate; with
    # no required-specialists set in the registry the fallback is "≥1
    # accept AND zero non-accepts".
    for i in range(3):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_ACCEPTED, (
        f"expected paper_accepted; got {out.current_stage.value}"
    )


def test_writing_revision_writes_auto_revisions_round(tmp_path: Path) -> None:
    """Spec 015 T042: writing-class action items trigger the engine
    adapter — project STAYS at PAPER_REVIEW with revision_spec_path
    set, NOT transitions to a transient stage."""
    project = _bootstrap(tmp_path)
    _make_record(
        tmp_path, project, reviewer_name="rev_a", verdict="minor_revision",
        action_items=[ActionItem.from_text("Fix typo in §2.", "writing")],
    )

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_REVIEW
    assert out.revision_spec_path is not None
    assert "auto-revisions" in out.revision_spec_path
    # The round dir exists on disk.
    spec_dir = tmp_path / out.revision_spec_path
    assert (spec_dir / "tasks.md").is_file()


def test_science_revision_routes_to_research_clarified_via_adapter(tmp_path: Path) -> None:
    """Spec 015 T042: science-class items produce a KickbackRecord
    whose to_stage = 'clarified' (research side). The adapter still
    writes a round dir; the project stays at PAPER_REVIEW with the
    revision_spec_path so the implementer can pick the science fix up."""
    project = _bootstrap(tmp_path)
    _make_record(
        tmp_path, project, reviewer_name="rev_a", verdict="major_revision_science",
        action_items=[ActionItem.from_text("Re-run baseline with N>5.", "science")],
    )

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_REVIEW
    assert out.revision_spec_path is not None


def test_fatal_routes_to_brainstormed(tmp_path: Path) -> None:
    """A FATAL action item is the only path that yanks the project out
    of PAPER_REVIEW — back to BRAINSTORMED with rationale appended."""
    project = _bootstrap(tmp_path)
    _make_record(
        tmp_path, project, reviewer_name="rev_a", verdict="fundamental_flaws",
        action_items=[ActionItem.from_text("Methodology is unsound.", "fatal")],
    )

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.BRAINSTORMED


def test_fundamental_flaws_legacy_routes_to_paper_fundamental_flaws(
    tmp_path: Path,
) -> None:
    """Legacy back-compat: prompt_version 1.0.x records without
    action_items still produce a winning_recommendation of
    'fundamental_flaws' that routes to PAPER_FUNDAMENTAL_FLAWS."""
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="fundamental_flaws")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_FUNDAMENTAL_FLAWS


def test_citation_blocks_paper_accept(tmp_path: Path) -> None:
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
    assert out.current_stage != Stage.PAPER_ACCEPTED, (
        "fabricated citation must block paper_accepted"
    )
