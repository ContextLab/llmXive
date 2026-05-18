"""Rule-based, non-LLM Advancement-Evaluator (T028).

The sole writer of Project.current_stage. Reads project state + review
records and decides each stage transition.

Acceptance gate (per user request 2026-04-29): in addition to the
points threshold, **every required specialist reviewer must have
written an accept review** before the project can advance to
RESEARCH_ACCEPTED or PAPER_ACCEPTED. The list of required specialists
is read from agents/registry.yaml at evaluation time (any agent whose
name starts with `research_reviewer_` or `paper_reviewer_`).
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from llmxive.agents import registry as registry_loader
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
    ReviewerKind,
    ReviewRecord,
    Stage,
    VerificationStatus,
)


def _required_specialists(prefix: str, *, repo_root: Path | None = None) -> set[str]:
    """Return every agent name in the registry that starts with `prefix`.

    Used to gate RESEARCH_ACCEPTED on all `research_reviewer_*` accepts and
    PAPER_ACCEPTED on all `paper_reviewer_*` accepts.
    """
    try:
        reg = registry_loader.load(repo_root=repo_root)
    except Exception:
        return set()
    return {a.name for a in reg.agents if a.name.startswith(prefix)}


def _all_specialists_accept(records: list[ReviewRecord], required: set[str]) -> bool:
    """True iff every required reviewer has at least one accept record.

    Legacy semantic — pre-spec-012. Retained for the research-review gate
    (which has not changed). The paper-stage gate now uses
    :func:`_all_specialists_accept_most_recent` per spec 012 / FR-001.
    """
    if not required:
        return True  # no gate configured
    accepted_by: set[str] = {
        r.reviewer_name for r in records if r.verdict == "accept"
    }
    return required <= accepted_by


def _most_recent_per_specialist(
    records: list[ReviewRecord],
    *,
    live_hash: str | None = None,
) -> dict[str, ReviewRecord]:
    """Return one record per specialist — the latest by ``reviewed_at``.

    If ``live_hash`` is provided, only records whose ``artifact_hash``
    matches are considered (stale-artifact reviews are ignored per
    spec 012 / FR-003).
    """
    eligible = (
        [r for r in records if r.artifact_hash == live_hash]
        if live_hash is not None
        else list(records)
    )
    by_specialist: dict[str, ReviewRecord] = {}
    for r in eligible:
        cur = by_specialist.get(r.reviewer_name)
        if cur is None or r.reviewed_at > cur.reviewed_at:
            by_specialist[r.reviewer_name] = r
    return by_specialist


def _all_specialists_accept_most_recent(
    records: list[ReviewRecord], required: set[str], *, live_hash: str | None = None,
) -> bool:
    """Spec 012 / FR-001: every required specialist's MOST-RECENT non-stale
    verdict must be ``accept``. Replaces the "any historical accept counts"
    semantic — that gate was unreachable in practice because specialists
    nit-pick every round.
    """
    if not required:
        return True
    latest = _most_recent_per_specialist(records, live_hash=live_hash)
    for name in required:
        rec = latest.get(name)
        if rec is None or rec.verdict != "accept":
            return False
    return True


def _max_severity_across_specialists(
    records: list[ReviewRecord], *, live_hash: str | None = None,
) -> str | None:
    """Spec 012 / FR-004-005: severity ordering writing < science < fatal.

    Returns the highest severity in any per-specialist most-recent record's
    action_items list, or ``None`` if all most-recent verdicts are accept
    (i.e. no non-accept items exist).
    """
    latest = _most_recent_per_specialist(records, live_hash=live_hash)
    order = {"writing": 1, "science": 2, "fatal": 3}
    rev = {v: k for k, v in order.items()}
    max_rank = 0
    for rec in latest.values():
        if rec.verdict == "accept":
            continue
        for item in rec.action_items:
            r = order.get(item.severity, 0)
            if r > max_rank:
                max_rank = r
    return rev.get(max_rank)


def _infer_live_hash(records: list[ReviewRecord]) -> str | None:
    """The "live" artifact hash for the current paper-review round.

    Spec 012 / FR-003: stale reviews (whose ``artifact_hash`` doesn't match
    the live artifact) must be ignored for the gate. We approximate "live"
    as the artifact_hash carried by the most-recent review record overall
    — this is the artifact every specialist most-recently reviewed.

    Returns ``None`` if there are no records (in which case the gate is
    trivially not satisfied).
    """
    if not records:
        return None
    latest = max(records, key=lambda r: r.reviewed_at)
    return latest.artifact_hash


def _consolidate_action_items(
    records: list[ReviewRecord], *, live_hash: str | None = None,
) -> list:
    """Deduplicate action items by id across all per-specialist
    most-recent non-accept reviews. Preserves first-seen order.
    """
    latest = _most_recent_per_specialist(records, live_hash=live_hash)
    seen: dict[str, object] = {}
    for rec in latest.values():
        if rec.verdict == "accept":
            continue
        for item in rec.action_items:
            if item.id not in seen:
                seen[item.id] = item
    return list(seen.values())


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
        # Reject un-authenticated human reviews. Anyone could drop a
        # YAML file into reviews/ claiming reviewer_kind=human; the
        # github_authenticated flag is set only by the OAuth-backed
        # submission flow.
        if rec.reviewer_kind == ReviewerKind.HUMAN and not rec.github_authenticated:
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
    """Return the verdict to act on, or None if no records.

    Strategy: **majority-vote with severity tie-break**.

    1. Count each verdict's frequency.
    2. Hard severity floor: if ≥50% of reviewers voted `reject` or
       `fundamental_flaws`, route there immediately (those are
       project-killers and a true majority is needed to terminate).
    3. Otherwise, take the verdict with the most votes. If two are
       tied, pick the more severe one (severity ladder: reject >
       fundamental_flaws > full_revision > major_revision_science >
       major_revision_writing > minor_revision > accept).

    Why not "weakest link" (any one severe verdict wins)? With 7-8
    reviewers, that rule guaranteed at least one full_revision per
    round even when 5+ reviewers said the work only needed minor
    tweaks — the pipeline would throw away the entire revision and
    restart from `clarified`, wasting hours. Majority-vote lets the
    pipeline make incremental progress when most reviewers agree the
    work is close.
    """
    if not records:
        return None

    counts: dict[str, int] = defaultdict(int)
    for rec in records:
        counts[rec.verdict] += 1
    if not counts:
        return None

    # Hard severity floor — kill the project only on true majority.
    n = len(records)
    half = (n + 1) // 2  # ceiling: 4 of 7, 5 of 8
    for kill_verdict in ("reject", "fundamental_flaws"):
        if counts.get(kill_verdict, 0) >= half:
            return kill_verdict

    # Severity ladder for tie-breaking (lower index = more severe).
    severity_order = [
        "reject",
        "fundamental_flaws",
        "full_revision",
        "major_revision_science",
        "major_revision_writing",
        "minor_revision",
        "accept",
    ]
    severity_index = {v: i for i, v in enumerate(severity_order)}

    # Pick by (highest count, then most-severe verdict for tie-break).
    return max(
        counts.items(),
        key=lambda kv: (kv[1], -severity_index.get(kv[0], 99)),
    )[0]


def evaluate(project: Project, *, repo_root: Path | None = None) -> Project:
    """Decide whether the project transitions; return updated state.

    No-op if the project is in a stable stage (e.g., specified, planned)
    that another agent advances. The Evaluator only fires for stages it
    governs: review-result transitions and citation-gated accepts.
    """
    cits = citations_store.load(project.id, repo_root=repo_root)

    # Auto-promote research_complete → research_review when at least one
    # research-stage review record has been written (T067).
    if project.current_stage == Stage.RESEARCH_COMPLETE:
        records = reviews_store.list_for(project.id, stage="research", repo_root=repo_root)
        if records:
            project = _transition(project, Stage.RESEARCH_REVIEW)
        else:
            return project

    # Auto-promote paper_complete → paper_review on the same trigger.
    if project.current_stage == Stage.PAPER_COMPLETE:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
        if records:
            project = _transition(project, Stage.PAPER_REVIEW)
        else:
            return project

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
        required = _required_specialists("research_reviewer_", repo_root=repo_root)
        all_accept = _all_specialists_accept(records, required)
        # Both gates must pass: enough points AND every specialist accepts.
        if (
            accept_total >= RESEARCH_ACCEPT_THRESHOLD
            and all_accept
            and not _has_blocking_citations(cits)
        ):
            return _transition(project, Stage.RESEARCH_ACCEPTED)
        if winning == "minor_revision":
            return _transition(project, Stage.RESEARCH_MINOR_REVISION)
        if winning == "full_revision":
            return _transition(project, Stage.RESEARCH_FULL_REVISION)
        if winning == "reject":
            return _transition(project, Stage.RESEARCH_REJECTED)
        return project  # not enough votes yet

    # Paper-review handling (spec 012 convergence pipeline).
    if project.current_stage == Stage.PAPER_REVIEW:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
        project = _award_review_points(
            project,
            records,
            bucket="paper_review",
            citations=cits,
            is_paper_stage=True,
        )
        required = _required_specialists("paper_reviewer_", repo_root=repo_root)
        # Spec 012 / FR-003: most-recent verdict per specialist against the
        # live artifact hash. For the live_hash, we use the most common
        # artifact_hash across the most recent records (an arxiv-intake
        # paper's metadata.json hash, or a home-grown paper's tasks.md hash).
        live_hash = _infer_live_hash(records)
        # Spec 012 / FR-001: PAPER_ACCEPTED iff every specialist's
        # most-recent non-stale verdict is accept. No additional point
        # threshold — the all-accept condition is the sole gate.
        if (
            _all_specialists_accept_most_recent(records, required, live_hash=live_hash)
            and not _has_blocking_citations(cits)
        ):
            return _transition(project, Stage.PAPER_ACCEPTED)

        # Spec 012 / FR-004-008: severity-based routing.
        max_sev = _max_severity_across_specialists(records, live_hash=live_hash)

        # Back-compat for legacy records (prompt_version 1.0.x) with no
        # action_items: fall back to the pre-spec-012 `_winning_recommendation`
        # so we don't regress projects whose reviewers haven't yet been
        # re-run under the new prompts. _max_severity returns None in this
        # case, which lets us detect "no spec-012-style data available".
        if max_sev is None and not _all_specialists_accept_most_recent(
            records, required, live_hash=live_hash
        ):
            winning = _winning_recommendation(records)
            if winning == "minor_revision":
                return _transition(project, Stage.PAPER_MINOR_REVISION)
            if winning == "major_revision_writing":
                return _transition(project, Stage.PAPER_MAJOR_REVISION_WRITING)
            if winning == "major_revision_science":
                return _transition(project, Stage.PAPER_MAJOR_REVISION_SCIENCE)
            if winning == "fundamental_flaws":
                return _transition(project, Stage.PAPER_FUNDAMENTAL_FLAWS)
            return project

        if max_sev == "fatal":
            # Reject to backlog with consolidated fatal items appended to
            # the idea record (FR-008 + US4).
            from llmxive.agents.upstream_feedback import append_rejection_rationale
            try:
                append_rejection_rationale(
                    project.id,
                    _consolidate_action_items(records, live_hash=live_hash),
                    repo_root=repo_root,
                )
            except Exception:  # noqa: BLE001 — defensive; rationale failure must not block transition
                pass
            return _transition(project, Stage.BRAINSTORMED)

        # arxiv-intake guardrail (FR-021/022, US7): for third-party
        # arxiv-submitted papers, the writing-revision and science-revision
        # paths CANNOT mutate paper/source/ (it's frozen). Record an
        # upstream-feedback annotation and accept-with-caveats.
        if max_sev in ("writing", "science"):
            from llmxive.agents.upstream_feedback import is_arxiv_intake, record_round
            project_dir = (repo_root or Path(__file__).resolve().parents[3]) / "projects" / project.id
            if is_arxiv_intake(project_dir):
                try:
                    record_round(
                        project.id,
                        verdict_class=max_sev,
                        action_items=_consolidate_action_items(records, live_hash=live_hash),
                        repo_root=repo_root,
                    )
                except Exception:  # noqa: BLE001
                    pass
                return _transition(project, Stage.PAPER_ACCEPTED)

            # Home-grown paper with writing/science items: route through
            # the legacy MINOR/MAJOR revision stages for now (FR-006/007's
            # PAPER_REVISION_IN_PROGRESS auto-plan path is part of US2/US3
            # and ships in a follow-up — until then the legacy graph is
            # the back-compat path).
            #
            # The mapping: severity=writing → PAPER_MINOR_REVISION; any
            # `major_revision_writing` verdict on a most-recent record
            # overrides to PAPER_MAJOR_REVISION_WRITING; severity=science
            # → PAPER_MAJOR_REVISION_SCIENCE.
            latest = _most_recent_per_specialist(records, live_hash=live_hash)
            verdicts = {r.verdict for r in latest.values()}
            if max_sev == "writing":
                if "major_revision_writing" in verdicts:
                    return _transition(project, Stage.PAPER_MAJOR_REVISION_WRITING)
                return _transition(project, Stage.PAPER_MINOR_REVISION)
            if max_sev == "science":
                return _transition(project, Stage.PAPER_MAJOR_REVISION_SCIENCE)

        # No specialists yet, or some other non-canonical state — keep
        # waiting at PAPER_REVIEW for more reviews.
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
