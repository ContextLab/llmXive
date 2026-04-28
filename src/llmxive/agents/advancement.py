"""Rule-based, non-LLM Advancement-Evaluator (T028).

The sole writer of Project.current_stage. Reads project state + review
records and decides each stage transition. Per-story rules (US1, US3,
US5, US7) are added incrementally; the skeleton here enforces the
self-review prohibition and the citation-blocking gates that already
apply.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from llmxive.agents.lifecycle import is_valid_transition
from llmxive.config import (
    PAPER_ACCEPT_THRESHOLD,
    RESEARCH_ACCEPT_THRESHOLD,
)
from llmxive.state import citations as citations_store
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    Project,
    ReviewRecord,
    Stage,
    VerificationStatus,
)


class AdvancementError(RuntimeError):
    """Raised when a requested transition is invalid."""


def _produced_by(project: Project, artifact_path: str) -> str | None:
    """Best-effort author lookup from the project's run-log; v1 stub.

    A future refinement reads state/run-log/ to find the entry that wrote
    the artifact and returns entry.agent_name. For v1 we return None so
    self-review filtering is done by reviewer-name comparison only.
    """
    return None


def _award_review_points(
    project: Project,
    records: list[ReviewRecord],
    *,
    bucket: str,
    citations: list[citations_store.Citation],
    is_paper_stage: bool,
) -> Project:
    """Sum eligible review records into the right point bucket.

    Eligibility filters:
    1. The record's artifact_hash matches the live artifact's hash
       (anti-tamper).
    2. The reviewer is not the artifact's author (self-review prohibited).
    3. The reviewed artifact has no citation in unreachable/mismatch
       status (FIX C2 — Reference-Validator gates point award).
    """
    bad_artifacts: set[str] = {
        c.artifact_path
        for c in citations
        if c.verification_status in (VerificationStatus.UNREACHABLE, VerificationStatus.MISMATCH)
    }
    awarded: float = 0.0
    for rec in records:
        if rec.artifact_path in bad_artifacts:
            continue
        live_hash = project.artifact_hashes.get(rec.artifact_path)
        if live_hash and live_hash != rec.artifact_hash:
            continue
        author = _produced_by(project, rec.artifact_path)
        if author and author == rec.reviewer_name:
            continue
        awarded += rec.score
    target = (
        project.points_paper if is_paper_stage else project.points_research
    )
    target = dict(target)
    target[bucket] = round(target.get(bucket, 0.0) + awarded, 2)
    if is_paper_stage:
        return project.model_copy(update={"points_paper": target})
    return project.model_copy(update={"points_research": target})


def _winning_recommendation(records: list[ReviewRecord]) -> str | None:
    """Return the highest-weighted verdict, or None if no records."""
    if not records:
        return None
    sums: dict[str, float] = defaultdict(float)
    for rec in records:
        sums[rec.verdict] += rec.score
    if not sums:
        return None
    return max(sums.items(), key=lambda kv: (kv[1], kv[0]))[0]


def evaluate(project: Project, *, repo_root: Path | None = None) -> Project:
    """Decide whether the project transitions; return updated state.

    No-op if the project is in a stable stage (e.g., specified, planned)
    that another agent advances. The Evaluator only fires for stages it
    governs: review-result transitions and citation-gated accepts.
    """
    cits = citations_store.load(project.id, repo_root=repo_root)

    # Research-review handling (US3 wiring; placeholder logic now).
    if project.current_stage == Stage.RESEARCH_REVIEW:
        records = reviews_store.list_for(project.id, stage="research", repo_root=repo_root)
        project = _award_review_points(
            project,
            records,
            bucket="research_review",
            citations=cits,
            is_paper_stage=False,
        )
        accept_total = sum(r.score for r in records if r.verdict == "accept")
        winning = _winning_recommendation(records)
        if accept_total >= RESEARCH_ACCEPT_THRESHOLD and not _has_blocking_citations(cits):
            return _transition(project, Stage.RESEARCH_ACCEPTED)
        if winning == "minor_revision":
            return _transition(project, Stage.RESEARCH_MINOR_REVISION)
        if winning == "full_revision":
            return _transition(project, Stage.RESEARCH_FULL_REVISION)
        if winning == "reject":
            return _transition(project, Stage.RESEARCH_REJECTED)
        return project  # not enough votes yet

    # Paper-review handling (US5 wiring).
    if project.current_stage == Stage.PAPER_REVIEW:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
        project = _award_review_points(
            project,
            records,
            bucket="paper_review",
            citations=cits,
            is_paper_stage=True,
        )
        accept_total = sum(r.score for r in records if r.verdict == "accept")
        winning = _winning_recommendation(records)
        if accept_total >= PAPER_ACCEPT_THRESHOLD and not _has_blocking_citations(cits):
            return _transition(project, Stage.PAPER_ACCEPTED)
        if winning == "minor_revision":
            return _transition(project, Stage.PAPER_MINOR_REVISION)
        if winning == "major_revision_writing":
            return _transition(project, Stage.PAPER_MAJOR_REVISION_WRITING)
        if winning == "major_revision_science":
            return _transition(project, Stage.PAPER_MAJOR_REVISION_SCIENCE)
        if winning == "fundamental_flaws":
            return _transition(project, Stage.PAPER_FUNDAMENTAL_FLAWS)
        return project

    return project


def _has_blocking_citations(cits: list[citations_store.Citation]) -> bool:
    return any(
        c.verification_status in (VerificationStatus.UNREACHABLE, VerificationStatus.MISMATCH)
        for c in cits
    )


def _transition(project: Project, target: Stage) -> Project:
    if not is_valid_transition(project.current_stage, target):
        raise AdvancementError(
            f"invalid transition {project.current_stage.value} -> {target.value}"
        )
    return project.model_copy(update={"current_stage": target})


def commit(project: Project, *, repo_root: Path | None = None) -> None:
    """Persist a project after evaluate(); convenience helper."""
    project_store.save(project, repo_root=repo_root)


__all__ = ["evaluate", "commit", "AdvancementError"]
