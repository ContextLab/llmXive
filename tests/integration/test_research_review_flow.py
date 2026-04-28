"""Integration test (T069): research-review voting routes correctly.

Pure file-fixture-driven; no LLM calls. Asserts that given synthetic
review records, the Advancement-Evaluator routes the project to the
correct next stage:

  * accept-vote total ≥ RESEARCH_ACCEPT_THRESHOLD → research_accepted
  * winning verdict 'minor_revision'              → research_minor_revision
  * winning verdict 'full_revision'               → research_full_revision
  * winning verdict 'reject'                      → research_rejected

Plus the citation-blocking gate: if any citation is in unreachable or
mismatch status, the project cannot reach research_accepted even with
sufficient accept votes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from llmxive.agents import advancement
from llmxive.config import RESEARCH_ACCEPT_THRESHOLD
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


PROJ_ID = "PROJ-001-review"


def _bootstrap(repo: Path) -> Project:
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)
    feature_dir = repo / "projects" / PROJ_ID / "specs" / "001-review"
    feature_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = feature_dir / "tasks.md"
    tasks_path.write_text("- [X] T001 done\n", encoding="utf-8")

    now = datetime.now(timezone.utc)
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
        stage="research",
        review_type="research",
        produced_by_agent=None,
        repo_root=repo,
    )
    return rec


def test_accept_threshold_advances_to_accepted(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    # Need RESEARCH_ACCEPT_THRESHOLD / 0.5 distinct LLM accepts.
    n_needed = int(RESEARCH_ACCEPT_THRESHOLD / 0.5) + 1  # one extra for safety
    for i in range(n_needed):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_ACCEPTED, (
        f"expected research_accepted; got {out.current_stage.value}"
    )


def test_minor_revision_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    # Two minor_revision votes (each 0.0), one accept (0.5). Sum:
    # accept_total = 0.5 (below threshold), winning verdict by total
    # weight: accept (0.5) > minor (0.0). Make minor_revision win by
    # weighting it higher? The current rule sorts by total weight; LLM
    # verdicts other than accept all carry 0.0 score. So a tie at 0.0
    # for non-accepts. To make minor_revision win unambiguously, we
    # need NO accept votes.
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="minor_revision")
    _make_record(tmp_path, project, reviewer_name="rev_b", verdict="minor_revision")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_MINOR_REVISION


def test_full_revision_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="full_revision")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_FULL_REVISION


def test_reject_winning(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    _make_record(tmp_path, project, reviewer_name="rev_a", verdict="reject")

    out = advancement.evaluate(project, repo_root=tmp_path)
    assert out.current_stage == Stage.RESEARCH_REJECTED


def test_citation_blocks_accept(tmp_path: Path) -> None:
    project = _bootstrap(tmp_path)
    n_needed = int(RESEARCH_ACCEPT_THRESHOLD / 0.5) + 1
    for i in range(n_needed):
        _make_record(tmp_path, project, reviewer_name=f"reviewer_{i}", verdict="accept")

    # Plant one fabricated citation.
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
    assert out.current_stage != Stage.RESEARCH_ACCEPTED, (
        "fabricated citation must block research_accepted"
    )
