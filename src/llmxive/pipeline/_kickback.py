"""Adaptive convergence-kickback routing + per-project cap (F-14 / F-20 Part B).

When a doc-stage convergence panel does NOT converge, ``_stage_panel`` writes a
generic ``convergence_kickback.yaml`` record into the stage's ``.specify/memory/``
dir carrying ``{to_stage, worst_severity, reason, unresolved_concerns, stage}``.

This module is the SSoT for the graph's consumption of that sentinel:

* :func:`consume_convergence_kickback` reads + DELETES the sentinel and returns
  the routing decision — the target content stage to auto-kick-back to, OR a
  human-escalation signal once the per-stage kickback count exceeds
  :data:`CONVERGENCE_KICKBACK_CAP`.
* The kickback count is tracked in a small ``kickback_count.yaml`` file keyed by
  the kicked-back *stage label* (lower-churn than a Project schema field and
  testable at the ``_decide_next_stage`` level). It is incremented on every
  adaptive kickback and reset when a project advances PAST the kicked-back
  stage (so a later legitimate kickback starts fresh).

Reserving ``human_input_needed.yaml`` for genuine human escalation (engine
failure + the cap-hit case here) keeps the two routes cleanly separated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

#: Maximum number of consecutive adaptive kickbacks at a single stage before
#: the project is escalated to ``human_input_needed`` instead of auto-retrying
#: (avoids an infinite flesh_out <-> spec loop). The Nth kickback that pushes
#: the count strictly ABOVE this cap escalates.
CONVERGENCE_KICKBACK_CAP = 3

#: Automated retry budget for unresolved-claim kickbacks (FR-013/014 / T021).
#: When ``convergence_kickback.yaml`` carries ``unresolved_claim=True``, the
#: graph routes the project back to the resolver stage (escalate=False) for up
#: to this many additional automated retries *before* falling back to the
#: ``CONVERGENCE_KICKBACK_CAP`` human-escalation path.  Kept near
#: ``CONVERGENCE_KICKBACK_CAP`` as the SSoT for both caps.
CLAIM_RETRY_BUDGET = 2

#: Spec 023 / FR-014: bounded automated retries for idea-stage rejections
#: (flesh-out "infeasible scope" + validator "rejected"). Each rejection
#: archives the idea and triggers a constrained re-brainstorm; after this
#: many failed regenerations the project takes the honest terminal
#: (``Stage.VALIDATOR_REJECTED`` — the idea backlog), NEVER a human
#: escalation. Kept with the other caps as the SSoT.
IDEA_RETRY_CAP = 3

_KICKBACK_COUNT_FILENAME = "kickback_count.yaml"
_CONVERGENCE_KICKBACK_FILENAME = "convergence_kickback.yaml"


@dataclass(frozen=True)
class KickbackDecision:
    """Outcome of consuming a ``convergence_kickback.yaml`` sentinel."""

    #: The content stage to auto-kick-back to (None when escalating).
    to_stage: str | None
    #: True once the per-stage cap is exceeded → route to human_input_needed.
    escalate: bool
    #: The kicked-back source stage label (for counter bookkeeping / reset).
    stage_label: str
    #: Human-facing reason carried from the kickback record.
    reason: str
    #: 1-based count of kickbacks at this stage AFTER this one.
    count: int
    #: The unresolved-concern bodies (``Concern.text`` strings) carried from the
    #: kickback record. Captured here BEFORE the sentinel is deleted so the graph
    #: can persist them for the content stage (flesh_out / brainstorm) — otherwise
    #: the panel's diagnosis is lost and the content agent re-elaborates the same
    #: flawed idea (the infinite spec↔flesh_out loop this field fixes).
    unresolved_concerns: tuple[str, ...] = ()


def _read_counts(memory_dir: Path) -> dict[str, int]:
    path = memory_dir / _KICKBACK_COUNT_FILENAME
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("kickback_count read failed for %s: %s", path, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}


def _write_counts(memory_dir: Path, counts: dict[str, int]) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    path = memory_dir / _KICKBACK_COUNT_FILENAME
    path.write_text(yaml.safe_dump(counts), encoding="utf-8")


def bump_count(memory_dir: Path, label: str) -> int:
    """Increment and return the persistent counter for ``label``.

    Shares ``kickback_count.yaml`` with the convergence-kickback counters
    (one counter file per memory dir, keyed by label — Constitution I).
    Used by the FR-014 idea-retry bound (labels ``idea_scope_reject`` /
    ``idea_validator_reject``)."""
    counts = _read_counts(memory_dir)
    new_count = counts.get(label, 0) + 1
    counts[label] = new_count
    memory_dir.mkdir(parents=True, exist_ok=True)
    _write_counts(memory_dir, counts)
    return new_count


def read_count(memory_dir: Path, label: str) -> int:
    """Current value of the persistent counter for ``label`` (0 if unset)."""
    return _read_counts(memory_dir).get(label, 0)


def reset_kickback_count(memory_dir: Path, stage_label: str) -> None:
    """Clear the kickback counter for ``stage_label`` (called when the project
    advances PAST the kicked-back stage so a later kickback starts fresh)."""
    counts = _read_counts(memory_dir)
    if stage_label in counts:
        del counts[stage_label]
        if counts:
            _write_counts(memory_dir, counts)
        else:
            # No counters left — remove the file entirely to stay tidy.
            path = memory_dir / _KICKBACK_COUNT_FILENAME
            try:
                path.unlink()
            except OSError:
                _write_counts(memory_dir, counts)


def consume_convergence_kickback(memory_dir: Path) -> KickbackDecision | None:
    """Read + DELETE a pending ``convergence_kickback.yaml`` and decide routing.

    Returns ``None`` when no sentinel is present. Otherwise increments the
    per-stage kickback counter; if the post-increment count strictly exceeds
    :data:`CONVERGENCE_KICKBACK_CAP`, the decision escalates to human input and
    the counter is reset (a human now owns the loop). The sentinel file is
    always consumed (deleted) after routing, mirroring the other graph
    sentinels (``research_question_revise.yaml`` etc.).
    """
    sentinel = memory_dir / _CONVERGENCE_KICKBACK_FILENAME
    if not sentinel.exists():
        return None

    try:
        payload = yaml.safe_load(sentinel.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("convergence_kickback read failed for %s: %s", sentinel, exc)
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    to_stage = payload.get("to_stage")
    stage_label = str(payload.get("stage") or "convergence")
    reason = str(payload.get("reason") or "convergence panel did not converge")
    # Capture the unresolved-concern bodies BEFORE the sentinel is unlinked
    # below — the graph persists these for the content stage so flesh_out
    # actually addresses the panel's diagnosis instead of re-elaborating the
    # same flawed idea.
    raw_concerns = payload.get("unresolved_concerns")
    concern_texts: tuple[str, ...] = ()
    if isinstance(raw_concerns, list):
        concern_texts = tuple(
            str(c["text"]).strip()
            for c in raw_concerns
            if isinstance(c, dict) and str(c.get("text") or "").strip()
        )
    # FR-013/014 / T021: unresolved-claim kickbacks get an extra automated retry
    # budget (CLAIM_RETRY_BUDGET) before the normal CONVERGENCE_KICKBACK_CAP
    # human-escalation path kicks in.  The sentinel writer sets this flag.
    is_claim_kickback: bool = bool(payload.get("unresolved_claim", False))

    counts = _read_counts(memory_dir)
    new_count = counts.get(stage_label, 0) + 1
    counts[stage_label] = new_count
    _write_counts(memory_dir, counts)

    # Consume the sentinel regardless of the routing decision.
    try:
        sentinel.unlink()
    except OSError as exc:  # pragma: no cover — telemetry only
        logger.warning("could not delete %s: %s", sentinel, exc)

    # Determine the effective cap for this kickback type.
    # Claim kickbacks: automated retries first (up to CLAIM_RETRY_BUDGET),
    # then the standard CONVERGENCE_KICKBACK_CAP continues normally so the
    # claim-retry window is *additional*, not a replacement.
    effective_cap = (
        CONVERGENCE_KICKBACK_CAP + CLAIM_RETRY_BUDGET
        if is_claim_kickback
        else CONVERGENCE_KICKBACK_CAP
    )

    if new_count > effective_cap or not isinstance(to_stage, str) or not to_stage:
        # Cap exceeded OR malformed target → human escalation; reset the
        # counter so a future re-entry starts clean.
        del counts[stage_label]
        if counts:
            _write_counts(memory_dir, counts)
        else:
            path = memory_dir / _KICKBACK_COUNT_FILENAME
            try:
                path.unlink()
            except OSError:
                _write_counts(memory_dir, counts)
        return KickbackDecision(
            to_stage=None,
            escalate=True,
            stage_label=stage_label,
            reason=reason,
            count=new_count,
            unresolved_concerns=concern_texts,
        )

    return KickbackDecision(
        to_stage=to_stage,
        escalate=False,
        stage_label=stage_label,
        reason=reason,
        count=new_count,
        unresolved_concerns=concern_texts,
    )


__all__ = [
    "CLAIM_RETRY_BUDGET",
    "CONVERGENCE_KICKBACK_CAP",
    "IDEA_RETRY_CAP",
    "KickbackDecision",
    "bump_count",
    "consume_convergence_kickback",
    "read_count",
    "reset_kickback_count",
]
