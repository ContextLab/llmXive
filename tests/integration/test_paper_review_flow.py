"""Integration test (T101): paper-review voting routes correctly.

Pure file-fixture-driven; no LLM calls. Asserts that given synthetic
paper review records, the Advancement-Evaluator routes the project
to the correct next stage:

  * accept-vote total ≥ PAPER_ACCEPT_THRESHOLD → paper_accepted
  * winning verdict 'minor_revision'              → paper_minor_revision
  * winning verdict 'major_revision_writing'      → paper_major_revision_writing
  * winning verdict 'major_revision_science'      → paper_major_revision_science
  * winning verdict 'fundamental_flaws'           → paper_fundamental_flaws

Plus the citation-blocking gate: if any citation is in unreachable or
mismatch status, the project cannot reach paper_accepted even with
sufficient accept votes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from llmxive.agents import advancement
from llmxive.config import PAPER_ACCEPT_THRESHOLD
from llmxive.state import citations as citations_store
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
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

    now = datetime.now(timezone.utc)
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
) -> ReviewRecord:
    score = 0.5 if verdict == "accept" else 0.0
    artifact_path = next(iter(project.artifact_hashes))
    rec = ReviewRecord(
        reviewer_name=reviewer_name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=artifact_path,
        artifact_hash=project.artifact_hashes[artifact_path],
        score=score,
        verdict=verdict,  # type: ignore[arg-type]
        feedback=f"{verdict} from {reviewer_name}",
        reviewed_at=datetime.now(timezone.utc),
        prompt_version="1.0.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
    )
    reviews_store.write(
        rec,
        body=f"Recommendation: {verdict}",
        stage="paper",
        review_type="paper",
        produced_by_agent=None,
        repo_root=repo,
    )
    return rec


def test_accept_threshold_advances_to_paper_accepted(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    n_needed = int(PAPER_ACCEPT_THRESHOLD / 0.5) + 1
    for i in range(n_needed):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_ACCEPTED, (
        f"expected paper_accepted; got {out.current_stage.value}"
    )


def test_minor_revision_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="minor_revision")
    _make_record(tmp_path, project, reviewer_name="rev_b", verdict="minor_revision")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_MINOR_REVISION


def test_major_revision_writing_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="major_revision_writing")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_MAJOR_REVISION_WRITING


def test_major_revision_science_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="major_revision_science")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_MAJOR_REVISION_SCIENCE


def test_fundamental_flaws_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="fundamental_flaws")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.PAPER_FUNDAMENTAL_FLAWS


def test_citation_blocks_paper_accept(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    n_needed = int(PAPER_ACCEPT_THRESHOLD / 0.5) + 1
    for i in range(n_needed):
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
        verified_at=datetime.now(timezone.utc),
    )
    citations_store.save(project.id, [bad], repo_root=tmp_path)

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage != Stage.PAPER_ACCEPTED, (
        "fabricated citation must block paper_accepted"
    )
