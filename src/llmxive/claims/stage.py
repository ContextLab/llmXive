"""Spec 020 — stage classification for the claim layer (FR-001).

Single source of truth for the *planning* vs *full-verification* distinction.

The speckit planning commands (specify/clarify → ``"spec"``, plan → ``"plan"``,
tasks → ``"tasks"``) produce documents that state the research question, method,
and references; they MUST NOT be held up verifying low-level empirical claims
(spec 020 Part A). Paper/research/implementation stages (``"paper_*"``) and any
unknown/None label fall through to FULL verification — the fail-safe direction is
toward *more* verification, never less.

Membership is exact: ``"paper_spec"`` is NOT a planning stage even though it
contains ``"spec"``.
"""

from __future__ import annotations

# The actual stage_label strings the planning commands emit, plus the conceptual
# aliases (specify/clarify) for forward-compatibility if a future command emits
# them. clarify_cmd.py emits "spec"; plan_cmd.py "plan"; tasks_cmd.py "tasks".
PLANNING_STAGE_LABELS: frozenset[str] = frozenset(
    {"spec", "specify", "clarify", "plan", "tasks"}
)


def is_planning_stage(stage_label: str | None) -> bool:
    """True iff ``stage_label`` denotes a planning stage (references-only + strip/smooth).

    ``None`` or any unrecognized label returns ``False`` (full verification) — the
    claim layer must never *skip* verification for an unknown stage.
    """
    if not stage_label:
        return False
    return stage_label in PLANNING_STAGE_LABELS


__all__ = ["PLANNING_STAGE_LABELS", "is_planning_stage"]
