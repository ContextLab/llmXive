"""Adapter from the two legacy paper-revision routing schemes → ``KickbackRecord``
(spec 015 T042, discrepancy #6).

llmXive accumulated TWO parallel revision-routing schemes before spec 015:

1. **graph.py transient-stage routing** (``_decide_next_stage``):
   ``research_minor_revision`` → ``tasked``;
   ``research_full_revision`` → ``clarified``;
   ``research_rejected`` → ``brainstormed``;
   ``paper_minor_revision`` → ``paper_tasked``;
   ``paper_major_revision_writing`` → ``paper_clarified``;
   ``paper_major_revision_science`` → ``clarified``;
   ``paper_fundamental_flaws`` → ``brainstormed``.

2. **advancement.py + revision_planner.py spec-012 scheme**:
   ``paper_revision_in_progress`` (transient) → ``ready_for_implementation``
   or ``paper_revision_blocked`` (operator unblocks via CLI).

Spec 015's convergence engine (:mod:`llmxive.convergence.kickback`) is the
NEW unified path: every reviewable step emits a ``KickbackRecord`` on
non-convergence, and adaptive severity routing replaces both legacy
schemes (``route_kickback`` walks ``worst_severity`` → ``ReviewSpec.kickback_routing``).

This module is the bridge: until the engine fully drives the pipeline
(T021 real-project integration), legacy outcomes can be converted to
``KickbackRecord`` so downstream tooling, dashboards, and the new
convergence-status surface (``status_reporter`` in T043) see ONE shape
for revision events regardless of which scheme produced them.

The legacy stages stay valid in the meantime — they are NOT deleted by
this adapter. Deletion happens at T021 when the engine becomes the sole
source of truth for revision routing.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .types import KickbackRecord, Severity

# --- Severity assignment per legacy outcome ------------------------------
#
# This map encodes what severity the engine WOULD have observed had it
# driven the same routing decision. ``research_rejected`` /
# ``paper_fundamental_flaws`` map to ``FATAL`` (engine routes them to
# ``brainstormed``); writing-class revisions map to ``WRITING``;
# methodology-class to ``METHODOLOGY``. The mapping is the SSoT for
# severity-vs-legacy correspondence used in tests + dashboards.

_LEGACY_GRAPH_ROUTING: dict[str, tuple[str, Severity, str]] = {
    # legacy_stage : (to_stage, severity, reason)
    "research_minor_revision": (
        "tasked", Severity.REQUIREMENT,
        "research review flagged minor revisions; re-task to address",
    ),
    "research_full_revision": (
        "clarified", Severity.METHODOLOGY,
        "research review flagged full revisions; re-plan (via clarified) to address",
    ),
    "research_rejected": (
        "brainstormed", Severity.FATAL,
        "research review rejected the project; back to brainstorm",
    ),
    "paper_minor_revision": (
        "paper_tasked", Severity.WRITING,
        "paper review flagged minor revisions; re-task paper to address",
    ),
    "paper_major_revision_writing": (
        "paper_clarified", Severity.WRITING,
        "paper review flagged writing-level revisions; re-clarify the paper spec",
    ),
    "paper_major_revision_science": (
        "clarified", Severity.SCIENCE,
        "paper review flagged science-root cause; kickback to research side",
    ),
    "paper_fundamental_flaws": (
        "brainstormed", Severity.FATAL,
        "paper review flagged fundamental flaws; back to brainstorm",
    ),
}

# --- Adapter (graph.py legacy scheme) ------------------------------------


def kickback_from_graph_stage(
    legacy_stage: str,
    *,
    project_id: str | None = None,
    artifact_links: list[str] | None = None,
) -> KickbackRecord | None:
    """Convert a graph.py transient revision stage to a ``KickbackRecord``.

    Returns ``None`` if ``legacy_stage`` is not one of the seven legacy
    transient stages. ``project_id`` (when provided) gets baked into the
    ``reason`` for traceability."""
    info = _LEGACY_GRAPH_ROUTING.get(legacy_stage)
    if info is None:
        return None
    to_stage, severity, reason = info
    return KickbackRecord(
        from_stage=legacy_stage,
        to_stage=to_stage,
        worst_severity=severity,
        unresolved_concerns=[],
        artifact_links=artifact_links or [],
        reason=(
            f"[legacy graph routing -> KickbackRecord adapter] {reason}"
            + (f" (project={project_id})" if project_id else "")
        ),
        created_at=datetime.now(UTC),
    )


# --- Adapter (advancement.py / revision_planner.py spec-012 scheme) ------


def kickback_from_revision_planner(
    final_outcome: str,
    *,
    revision_spec_path: str | None = None,
    project_id: str | None = None,
) -> KickbackRecord | None:
    """Convert a spec-012 ``revision_planner`` outcome to a ``KickbackRecord``.

    ``ready_for_implementation`` and ``paper_revision_blocked`` are the
    two legitimate outcomes; both produce a KickbackRecord describing
    where the project actually went. ``ready_for_implementation`` is a
    forward (NOT a kickback) — it gets a ``WRITING`` severity and the
    ``revision_spec_path`` in artifact_links so downstream tooling can
    pick up the planned revision; ``paper_revision_blocked`` is a
    blocked state needing operator unblock → ``FATAL`` severity."""
    if final_outcome == "ready_for_implementation":
        return KickbackRecord(
            from_stage="paper_revision_in_progress",
            to_stage="ready_for_implementation",
            worst_severity=Severity.WRITING,
            unresolved_concerns=[],
            artifact_links=[revision_spec_path] if revision_spec_path else [],
            reason=(
                "[legacy revision_planner -> KickbackRecord adapter] "
                "revision planner produced a revision spec; project moves to "
                "ready_for_implementation"
                + (f" (project={project_id})" if project_id else "")
            ),
            created_at=datetime.now(UTC),
        )
    if final_outcome == "paper_revision_blocked":
        return KickbackRecord(
            from_stage="paper_revision_in_progress",
            to_stage="paper_revision_blocked",
            worst_severity=Severity.FATAL,
            unresolved_concerns=[],
            artifact_links=[],
            reason=(
                "[legacy revision_planner -> KickbackRecord adapter] "
                "revision planner could not produce a revision spec; "
                "operator must unblock via `llmxive unblock-revision`"
                + (f" (project={project_id})" if project_id else "")
            ),
            created_at=datetime.now(UTC),
        )
    return None


# --- Migration documentation -----------------------------------------------


def legacy_revision_stages() -> frozenset[str]:
    """The set of legacy revision-stage names that this adapter recognizes
    (graph.py scheme + spec-012 scheme combined). Useful for tests + audit
    sweeps that need to know "what stages does the engine NOT yet own"."""
    return frozenset(_LEGACY_GRAPH_ROUTING) | frozenset({
        "paper_revision_in_progress",
        "ready_for_implementation",
        "paper_revision_blocked",
    })


__all__ = [
    "kickback_from_graph_stage",
    "kickback_from_revision_planner",
    "legacy_revision_stages",
]
