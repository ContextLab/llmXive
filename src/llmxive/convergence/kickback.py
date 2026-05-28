"""Adaptive kickback routing (spec 015 T026, #239).

Maps the worst unresolved concern severity to a prior stage via the step's
``ReviewSpec.kickback_routing`` and emits a fully-provenanced ``KickbackRecord``.
Replaces both legacy revision-routing schemes (graph transient stages +
advancement.py spec-012) — see contracts/kickback-record.md.
"""

from __future__ import annotations

from .types import (
    Concern,
    KickbackRecord,
    ProgressRecord,
    ReviewSpec,
    Severity,
    severity_rank,
    worst_severity,
)

# Severities ordered least->most serious (mirrors types._SEVERITY_ORDER).
_ORDER: tuple[Severity, ...] = (
    Severity.TRIVIAL, Severity.CODE, Severity.WRITING, Severity.REQUIREMENT,
    Severity.METHODOLOGY, Severity.SCIENCE, Severity.FATAL,
)


def _nearest_routing(routing: dict[Severity, str], worst: Severity) -> str:
    """Resolve a target stage for ``worst`` even if it has no exact routing entry:
    prefer the nearest-defined LOWER severity, else the nearest higher one."""
    if worst in routing:
        return routing[worst]
    rank = severity_rank(worst)
    lower = [s for s in routing if severity_rank(s) <= rank]
    if lower:
        return routing[max(lower, key=severity_rank)]
    higher = [s for s in routing if severity_rank(s) > rank]
    if higher:
        return routing[min(higher, key=severity_rank)]
    raise ValueError(f"ReviewSpec for stage {worst!r} has empty kickback_routing")


def route_kickback(spec: ReviewSpec, unresolved: list[Concern]) -> KickbackRecord:
    """Pick the worst unresolved severity, map it to a prior stage, and emit a
    KickbackRecord carrying full provenance (FR-014)."""
    if not unresolved:
        raise ValueError("route_kickback() requires at least one unresolved concern")
    worst = worst_severity([c.severity for c in unresolved])
    to_stage = _nearest_routing(spec.kickback_routing, worst)
    artifact_links = sorted({c.artifact for c in unresolved} | set(spec.artifacts))
    reason = (
        f"{len(unresolved)} concern(s) remained unresolved after {spec.max_rounds} "
        f"round(s) at stage '{spec.stage}'; worst unresolved severity = "
        f"'{worst.value}'. Routing to '{to_stage}' with full provenance so the next "
        f"worker can address the root cause."
    )
    return KickbackRecord(
        from_stage=spec.stage,
        to_stage=to_stage,
        worst_severity=worst,
        unresolved_concerns=list(unresolved),
        artifact_links=artifact_links,
        reason=reason,
    )


def progress_record(
    kickback_index: int,
    unresolved: list[Concern],
    previous_unresolved_ids: set[str] | None,
) -> ProgressRecord:
    """Snapshot per-kickback progress (FR-017): there is no global cap, but a
    non-improving cycle (the same unresolved set recurring) is made inspectable."""
    ids = sorted({c.id for c in unresolved})
    if previous_unresolved_ids is None:
        improved = True  # first kickback — nothing to compare against yet
    else:
        improved = set(ids) != previous_unresolved_ids
    return ProgressRecord(
        kickback_index=kickback_index,
        unresolved_concern_ids=ids,
        improved=improved,
    )


__all__ = ["progress_record", "route_kickback"]
