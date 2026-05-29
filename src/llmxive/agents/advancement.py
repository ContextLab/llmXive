"""Rule-based, non-LLM Advancement-Evaluator (T028).

The sole writer of Project.current_stage. Reads project state + review
records and decides each stage transition.

Acceptance gate (per user request 2026-04-29): in addition to the
points threshold, **every required specialist reviewer must have
written an accept review** before the project can advance to
RESEARCH_ACCEPTED or PAPER_ACCEPTED. The list of required specialists
is read from agents/registry.yaml at evaluation time (any agent whose
name starts with `research_reviewer_` or `paper_reviewer_`).

Two distinct rejection semantics (post spec-015 T042 + maintainer review):

  * **Engine kickback** (the modern path): a panel surfaces specific,
    actionable concerns; the engine writes ``auto-revisions/round-N/``
    with per-concern tasks; the project STAYS at RESEARCH_REVIEW or
    PAPER_REVIEW with ``revision_spec_path`` set; the implementer
    picks up the round + applies the revisions. This is FORMATIVE
    feedback — "fix these specific things and try again."

  * **Terminal-judgment stages** (kept, NOT folded into engine):
    ``RESEARCH_REJECTED``, ``RESEARCH_FULL_REVISION``, and
    ``PAPER_FUNDAMENTAL_FLAWS`` are retained because they encode a
    SUMMATIVE editorial verdict that the engine kickback shape can't
    represent:

      - ``RESEARCH_REJECTED`` — winning recommendation is ``reject``;
        the panel judges the submission isn't redeemable in its
        current shape. The project transitions back to BRAINSTORMED
        (lifecycle.ALLOWED_TRANSITIONS) so the author can re-pitch
        from scratch.
      - ``RESEARCH_FULL_REVISION`` — winning recommendation is
        ``full_revision``; the panel asks for ground-up rewrite, not
        a per-concern revision. Transitions back to CLARIFIED.
      - ``PAPER_FUNDAMENTAL_FLAWS`` — the paper-track equivalent of
        ``RESEARCH_REJECTED``; transitions back to BRAINSTORMED.

    These stages are surfaced in ``web_data.py`` as the public
    "rejected" status — the project tracker MUST be able to render
    them as distinct from active projects. Folding them into engine
    kickback would lose that public-status distinction AND would
    require the engine to be able to represent "panel said REJECT
    outright," which the per-concern shape can't.

    The codepath at lines ~365-368 (winning_recommendation == "reject"
    / "full_revision") is the live producer of these stages for
    legacy records that pre-date the engine; new engine-produced
    records use the kickback path below. The two paths coexist
    deliberately.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from llmxive.agents import registry as registry_loader
from llmxive.agents.lifecycle import is_valid_transition

# Spec 015 T041 / FR-019: the RESEARCH_ACCEPT_THRESHOLD / PAPER_ACCEPT_THRESHOLD
# point gates were removed; advancement no longer reads any point threshold from
# config. The sole gate is unanimous LLM-panel acceptance.
from llmxive.state import citations as citations_store
from llmxive.state import project as project_store
from llmxive.state import reviews as reviews_store
from llmxive.types import (
    Project,
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

    "No required specialists configured" (empty ``required``) means the
    registry didn't load. The defensible default is to require at least
    one accept record — never trivially accept on a vacuous gate.
    """
    if not required:
        # Defensive: with no required-set, only auto-pass when there ARE
        # accept records AND no non-accept records. Otherwise return False
        # so the severity branch handles non-accept verdicts.
        if not records:
            return False
        return all(r.verdict == "accept" for r in records)
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


def _produced_by(
    project: Project, artifact_path: str, *, repo_root: Path | None = None,
) -> str | None:
    """Return the agent that most-recently wrote ``artifact_path`` for this
    project, by scanning ``state/run-log/<YYYY-MM>/*.jsonl`` (spec 015 T025 /
    FR-018: self-review prevention — previously a stub that returned None).

    Match policy: an entry "wrote" the artifact iff its ``outputs`` list
    contains the path. Comparison is exact, then suffix (so a callsite that
    stores ``projects/PROJ-X/code/foo.py`` matches a run-log output recorded as
    ``code/foo.py`` and vice-versa). Returns the ``agent_name`` of the LATEST
    matching entry, or ``None`` if no run-log evidence exists.

    ``repo_root`` overrides the default state-root resolution for tests; in
    production callers omit it and the path falls back to the repo's own state/.
    """
    from pathlib import Path as _Path

    from llmxive.state.runlog import _state_root  # type: ignore[attr-defined]

    try:
        state_dir = (_Path(repo_root) / "state") if repo_root is not None else _state_root()
        log_root = state_dir / "run-log"
    except Exception:
        return None
    if not log_root.is_dir():
        return None

    def _matches(outputs: list[str]) -> bool:
        target = artifact_path
        for o in outputs:
            if o == target:
                return True
            # Suffix-match either direction to tolerate relative-vs-absolute
            # bookkeeping differences.
            if target.endswith(o) or o.endswith(target):
                return True
            # Path-segment compare for robustness against leading "./" etc.
            try:
                if _Path(o).as_posix().endswith(_Path(target).as_posix()):
                    return True
            except (TypeError, ValueError):
                pass
        return False

    from llmxive.types import RunLogEntry
    latest_agent: str | None = None
    latest_ended = None
    for month_dir in sorted(log_root.iterdir(), reverse=True):
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in sorted(month_dir.glob("*.jsonl"), reverse=True):
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = RunLogEntry.model_validate_json(line)
                except Exception:
                    continue
                if entry.project_id != project.id:
                    continue
                if not _matches(entry.outputs):
                    continue
                if latest_ended is None or entry.ended_at > latest_ended:
                    latest_ended = entry.ended_at
                    latest_agent = entry.agent_name
    return latest_agent


# Spec 015 T041 / FR-019: `_award_review_points` was REMOVED with the point
# system. Unanimous LLM-panel acceptance is now the sole gate; human and
# simulated-personality reviews are advisory inputs via stage-aware triage
# (`llmxive.convergence.triage`), never points. The `points_research` /
# `points_paper` fields on Project are retained on disk for back-compat but no
# advancement-decision path reads them.


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

    # Research-review handling.
    # Spec 015 T041 / FR-019/FR-020: point system REMOVED. The sole gate is now
    # unanimous LLM-panel acceptance (every required research_reviewer_* must
    # have an accept record), matching the paper-side gate. No accumulated
    # threshold, no _award_review_points call. Human / simulated-personality
    # reviews are advisory inputs via stage-aware triage, never points.
    #
    # Spec 015 T042 / FR-034: the 3 transient research-revision stages
    # (RESEARCH_MINOR_REVISION + reuse of full / rejected) were deleted.
    # The convergence engine is the sole inter-stage revision driver:
    # on non-unanimous-accept we emit a KickbackRecord routed by adaptive
    # severity to a stable stage (TASKED/CLARIFIED/BRAINSTORMED) via
    # ``llmxive.convergence.revision_adapter.kickback_to_revision_spec``.
    if project.current_stage == Stage.RESEARCH_REVIEW:
        records = reviews_store.list_for(project.id, stage="research", repo_root=repo_root)
        winning = _winning_recommendation(records)
        required = _required_specialists("research_reviewer_", repo_root=repo_root)
        all_accept = _all_specialists_accept(records, required)
        has_any_accept = any(r.verdict == "accept" for r in records)
        has_any_non_accept = any(r.verdict != "accept" for r in records)
        unanimous = all_accept and (
            bool(required) or (has_any_accept and not has_any_non_accept)
        )
        if unanimous and not _has_blocking_citations(cits):
            return _transition(project, Stage.RESEARCH_ACCEPTED)
        # FATAL judgments still need to be representable. The engine path
        # below routes the rest; here we keep the (rare) full-reject and
        # full-revision codepaths so a winning_recommendation of `reject`
        # / `full_revision` is honored on records that pre-date the engine.
        if winning == "reject":
            return _transition(project, Stage.RESEARCH_REJECTED)
        if winning == "full_revision":
            return _transition(project, Stage.RESEARCH_FULL_REVISION)
        # Spec 015 T042 engine path: a winning `minor_revision` (or any
        # other non-accept) now triggers the convergence-adapter kickback.
        # We don't run the engine itself here (advancement is a non-LLM
        # evaluator) — instead we project the available action items
        # straight onto a synthetic KickbackRecord whose worst-severity
        # adapts the legacy verdict, and let the adapter write the
        # auto-revisions dir for the implementer to pick up. The PROJECT
        # STAYS at RESEARCH_REVIEW; the implementer transitions it back
        # out after applying the revision.
        consolidated = _consolidate_action_items(records)
        if consolidated:
            from llmxive.convergence.revision_adapter import (
                kickback_to_revision_spec,
            )
            from llmxive.convergence.types import (
                Concern,
                KickbackRecord,
                Severity,
                from_legacy_severity,
                worst_severity,
            )
            engine_concerns = [
                Concern(
                    id=str(getattr(it, "id", "") or "000000000000")[:12].ljust(12, "0"),
                    reviewer="research_reviewer",
                    severity=from_legacy_severity(
                        getattr(it, "severity", "writing") or "writing"
                    ),
                    artifact=f"projects/{project.id}/specs/",
                    location="",
                    # Spec-015: Concern.text is now ``min_length=1``.
                    # ActionItem.text is already non-empty, but legacy
                    # records (without action_items) may pass through
                    # here with an empty fallback. Use an explicit
                    # marker rather than risk ValidationError.
                    text=(getattr(it, "text", "") or "").strip()
                         or "<no text on legacy action item>",
                    round=1,
                )
                for it in consolidated
            ]
            worst = worst_severity([c.severity for c in engine_concerns])
            kb = KickbackRecord(
                from_stage="research_review",
                to_stage=("tasked" if worst in {Severity.WRITING, Severity.REQUIREMENT, Severity.CODE}
                         else ("clarified" if worst in {Severity.METHODOLOGY}
                               else "brainstormed")),
                worst_severity=worst,
                unresolved_concerns=engine_concerns,
                artifact_links=[f"projects/{project.id}/specs/"],
                reason=(
                    "advancement.evaluate: research-review non-convergence; "
                    "routing via engine adapter."
                ),
            )
            spec_dir = kickback_to_revision_spec(
                kb,
                project_id=project.id,
                repo_root=repo_root or Path(__file__).resolve().parents[3],
            )
            rel = spec_dir.relative_to(
                repo_root or Path(__file__).resolve().parents[3]
            )
            return project.model_copy(update={
                "current_stage": Stage.RESEARCH_REVIEW,
                "revision_spec_path": str(rel),
            })
        return project  # not enough votes / no action items yet

    # Paper-review handling (spec 012 convergence pipeline; spec 015 T041 removed
    # the redundant _award_review_points bookkeeping — the all-specialists-accept
    # gate was always the actual decision).
    if project.current_stage == Stage.PAPER_REVIEW:
        records = reviews_store.list_for(project.id, stage="paper", repo_root=repo_root)
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

        # Spec 015 T042 / FR-034: the 3 transient paper-revision stages
        # (PAPER_MINOR_REVISION, PAPER_MAJOR_REVISION_WRITING/SCIENCE)
        # + the 3 spec-012 stages (PAPER_REVISION_IN_PROGRESS,
        # READY_FOR_IMPLEMENTATION, PAPER_REVISION_BLOCKED) were ALL
        # deleted. The convergence engine + adapter is the SOLE inter-
        # stage revision driver: on non-convergence we synthesize a
        # KickbackRecord, run it through
        # :func:`kickback_to_revision_spec` to write an auto-revisions
        # round dir, and KEEP the project at PAPER_REVIEW with
        # ``revision_spec_path`` set so the implementer picks it up.
        # On classifiable diagnostic failures the implementer's failsafe
        # itself writes the next round; on UNKNOWN failures it routes
        # to ``Stage.AGENT_BLOCKED``.
        #
        # Back-compat: if a record set is legacy-only (no action_items),
        # we still need to make a routing decision. We fall back to
        # `_winning_recommendation` for those records and route the
        # FATAL judgments through legacy stages that still exist
        # (RESEARCH_REJECTED-equivalent: PAPER_FUNDAMENTAL_FLAWS;
        # rejection-to-backlog: BRAINSTORMED via FATAL severity).
        if max_sev is None and not _all_specialists_accept_most_recent(
            records, required, live_hash=live_hash
        ):
            winning = _winning_recommendation(records)
            if winning == "fundamental_flaws":
                return _transition(project, Stage.PAPER_FUNDAMENTAL_FLAWS)
            # legacy minor / major rev → engine kickback path below
            # with a synthesized SCIENCE severity for major_science and
            # WRITING for the others.
            if winning in {"minor_revision", "major_revision_writing"}:
                max_sev = "writing"
            elif winning == "major_revision_science":
                max_sev = "science"
            else:
                return project  # not enough info yet

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
            except Exception:
                pass
            return _transition(project, Stage.BRAINSTORMED)

        if max_sev in ("writing", "science"):
            from llmxive.agents.upstream_feedback import is_arxiv_intake, record_round
            from llmxive.convergence.revision_adapter import (
                kickback_to_revision_spec,
            )
            from llmxive.convergence.types import (
                Concern,
                KickbackRecord,
                Severity,
                from_legacy_severity,
                worst_severity,
            )
            project_dir = (repo_root or Path(__file__).resolve().parents[3]) / "projects" / project.id
            if is_arxiv_intake(project_dir):
                # Preserve the upstream_feedback annotation for diagnostics
                # but DON'T short-circuit to PAPER_ACCEPTED. Fall through
                # to the engine-adapter path below.
                try:
                    record_round(
                        project.id,
                        verdict_class=max_sev,
                        action_items=_consolidate_action_items(records, live_hash=live_hash),
                        repo_root=repo_root,
                    )
                except Exception:
                    pass

            consolidated = _consolidate_action_items(records, live_hash=live_hash)
            if not consolidated:
                # Nothing actionable yet — stay at PAPER_REVIEW for more
                # reviews to arrive.
                return project
            engine_concerns = [
                Concern(
                    id=str(getattr(it, "id", "") or "000000000000")[:12].ljust(12, "0"),
                    reviewer="paper_reviewer",
                    severity=from_legacy_severity(
                        getattr(it, "severity", "writing") or "writing"
                    ),
                    artifact=f"projects/{project.id}/paper/source/",
                    location="",
                    # Spec-015: Concern.text is now ``min_length=1`` —
                    # see the research_reviewer branch above for rationale.
                    text=(getattr(it, "text", "") or "").strip()
                         or "<no text on legacy action item>",
                    round=1,
                )
                for it in consolidated
            ]
            worst = worst_severity([c.severity for c in engine_concerns])
            kb = KickbackRecord(
                from_stage="paper_review",
                to_stage=("paper_tasked" if worst in {
                    Severity.WRITING, Severity.REQUIREMENT, Severity.CODE,
                } else ("paper_clarified" if worst == Severity.METHODOLOGY
                        else ("clarified" if worst == Severity.SCIENCE
                              else "brainstormed"))),
                worst_severity=worst,
                unresolved_concerns=engine_concerns,
                artifact_links=[f"projects/{project.id}/paper/source/"],
                reason=(
                    "advancement.evaluate: paper-review non-convergence; "
                    "routing via engine adapter."
                ),
            )
            repo = repo_root or Path(__file__).resolve().parents[3]
            spec_dir = kickback_to_revision_spec(
                kb,
                project_id=project.id,
                repo_root=repo,
            )
            rel = spec_dir.relative_to(repo)
            return project.model_copy(update={
                "current_stage": Stage.PAPER_REVIEW,
                "revision_spec_path": str(rel),
            })

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


__all__ = ["AdvancementError", "commit", "evaluate"]
