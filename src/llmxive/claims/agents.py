"""T041 (spec 016, FR-001) — the maintained registry of claim-producing agents.

Every pipeline stage that writes a *document* can introduce a factual claim, so
every such stage must be covered by the claim-verification layer. The layer's
primary coverage mechanism is path-based: the shared document-write chokepoint
(``speckit.slash_command._validate_artifact_citations``) runs on EVERY ``.md`` /
``.tex`` artifact any stage produces, so coverage does not depend on
enumerating stages. This registry is the explicit, reviewable SSoT list of those
stages — used to assert (in tests) that no doc-producing stage is omitted, and
to document the surface the layer is responsible for.

If a new document-producing stage is added to the pipeline, add it here.
"""

from __future__ import annotations

# Each entry: (stage_id, human description). stage_id matches the slash-command
# / convergence stage labels used elsewhere in the pipeline.
CLAIM_PRODUCING_AGENTS: tuple[tuple[str, str], ...] = (
    ("spec", "Specification author (research spec.md)"),
    ("clarify", "Clarification author (spec clarifications)"),
    ("plan", "Implementation-plan author (plan.md)"),
    ("tasks", "Task-list author (tasks.md)"),
    ("implement", "Implementation/analysis author (impl summaries + results)"),
    ("flesh_out", "Idea flesh-out author (technical design document)"),
    ("paper_spec", "Paper specification author"),
    ("paper_clarify", "Paper clarification author"),
    ("paper", "Paper author (manuscript body, results, discussion)"),
    ("results_summary", "Results/summary producer (empirical-result reporters)"),
)

CLAIM_PRODUCING_STAGE_IDS: frozenset[str] = frozenset(a[0] for a in CLAIM_PRODUCING_AGENTS)


def is_claim_producing(stage_id: str) -> bool:
    """True iff ``stage_id`` is a registered claim-producing stage."""
    return stage_id in CLAIM_PRODUCING_STAGE_IDS


__all__ = [
    "CLAIM_PRODUCING_AGENTS",
    "CLAIM_PRODUCING_STAGE_IDS",
    "is_claim_producing",
]
