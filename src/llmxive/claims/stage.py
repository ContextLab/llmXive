"""Spec 020 — stage classification for the claim layer (FR-001).

Single source of truth for the *planning* vs *full-verification* distinction.

The speckit planning commands (specify/clarify → ``"spec"``, plan → ``"plan"``,
tasks → ``"tasks"``) produce documents that state the research question, method,
and references; they MUST NOT be held up verifying low-level empirical claims
(spec 020 Part A). Paper/research/implementation stages (``"paper_*"``) and any
unknown/None label fall through to FULL verification — the fail-safe direction is
toward *more* verification, never less.

Membership is exact: ``"paper_spec"`` is NOT a planning stage even though it
contains ``"spec"``. Independently, known research planning artifact paths retain
their role when the implementer edits them; the producer label does not turn a
runbook's expected outputs into external factual claims.
"""

from __future__ import annotations

from pathlib import PurePosixPath

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


def is_research_planning_artifact(artifact_path: str, project_id: str) -> bool:
    """Known project planning documents retain their role when edited later.

    Match the exact research Spec Kit layout, never paper/results documents or
    an arbitrary file that merely shares a planning basename.
    """
    path = PurePosixPath(artifact_path)
    return (
        str(path) == artifact_path
        and ".." not in path.parts
        and len(path.parts) == 5
        and path.parts[:3] == ("projects", project_id, "specs")
        and path.name in {"spec.md", "plan.md", "research.md", "data-model.md", "quickstart.md"}
    )


__all__ = ["PLANNING_STAGE_LABELS", "is_planning_stage", "is_research_planning_artifact"]
