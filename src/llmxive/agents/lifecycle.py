"""Lifecycle stage machine (T027).

Skeleton: defines the 30+ stage enum (re-exported from types.Stage) and
the allowed-transition map. Per-story extensions (T056, T067, T094,
T100) populate the map; the Advancement-Evaluator Agent consults it.
"""

from __future__ import annotations

from typing import Iterable

from llmxive.types import Stage


# Stage transition map: source stage -> set of allowed target stages.
# Populated incrementally as user stories are implemented; the
# Advancement-Evaluator refuses any transition not declared here.
ALLOWED_TRANSITIONS: dict[Stage, set[Stage]] = {
    # Idea-generation phase (T056 will add details for transitions through
    # this section; for now the structural skeleton is here).
    # Allow direct BRAINSTORMED → FLESH_OUT_COMPLETE when the FleshOut
    # agent finishes in one tick. The IN_PROGRESS intermediate is an
    # optional checkpoint for long-running flesh-out work.
    Stage.BRAINSTORMED: {Stage.FLESH_OUT_IN_PROGRESS, Stage.FLESH_OUT_COMPLETE, Stage.HUMAN_INPUT_NEEDED},
    Stage.FLESH_OUT_IN_PROGRESS: {Stage.FLESH_OUT_COMPLETE, Stage.HUMAN_INPUT_NEEDED},
    Stage.FLESH_OUT_COMPLETE: {
        # spec 003 / D10: research_question_validator inserted between
        # flesh_out and project_initializer. The validator emits one of
        # three outcomes:
        #   validated         → VALIDATED → PROJECT_INITIALIZED
        #   validator_revise  → FLESH_OUT_IN_PROGRESS (re-flesh_out)
        #   validator_rejected → BRAINSTORMED (re-brainstorm)
        Stage.VALIDATED,
        Stage.FLESH_OUT_IN_PROGRESS,  # validator_revise rollback
        Stage.HUMAN_INPUT_NEEDED,
        Stage.BRAINSTORMED,  # scope rejection or validator_rejected rolls back
        # Legacy direct path retained for backward compat (e.g., a
        # flesh_out_complete project that pre-dates the validator stage).
        Stage.PROJECT_INITIALIZED,
    },
    Stage.VALIDATED: {Stage.PROJECT_INITIALIZED, Stage.HUMAN_INPUT_NEEDED},
    # Per-project research Spec Kit pipeline (US1):
    Stage.PROJECT_INITIALIZED: {Stage.SPECIFIED},
    # The CLARIFY_IN_PROGRESS / ANALYZE_IN_PROGRESS intermediates are
    # optional checkpoints used by long-running operations; the
    # Clarifier and Tasker may transition directly to the next stable
    # stage when they complete in one tick.
    Stage.SPECIFIED: {Stage.CLARIFY_IN_PROGRESS, Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED},
    Stage.CLARIFY_IN_PROGRESS: {Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED},
    Stage.CLARIFIED: {Stage.PLANNED, Stage.HUMAN_INPUT_NEEDED},
    Stage.PLANNED: {Stage.TASKED, Stage.HUMAN_INPUT_NEEDED},
    Stage.TASKED: {Stage.ANALYZE_IN_PROGRESS, Stage.ANALYZED},
    Stage.ANALYZE_IN_PROGRESS: {Stage.ANALYZED, Stage.HUMAN_INPUT_NEEDED},
    Stage.ANALYZED: {Stage.IN_PROGRESS},
    Stage.IN_PROGRESS: {Stage.RESEARCH_COMPLETE, Stage.IN_PROGRESS, Stage.HUMAN_INPUT_NEEDED},
    # research_complete is now a brief checkpoint where the
    # specialist reviewers run before research_review, so we allow
    # the same outgoing transitions as research_review (review
    # records already exist on disk; advancement_evaluate decides).
    Stage.RESEARCH_COMPLETE: {
        Stage.RESEARCH_REVIEW,
        Stage.RESEARCH_ACCEPTED,
        Stage.RESEARCH_MINOR_REVISION,
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
    },
    # Research-quality review (US3):
    Stage.RESEARCH_REVIEW: {
        Stage.RESEARCH_ACCEPTED,
        Stage.RESEARCH_MINOR_REVISION,
        Stage.RESEARCH_FULL_REVISION,
        Stage.RESEARCH_REJECTED,
    },
    Stage.RESEARCH_ACCEPTED: {Stage.PAPER_DRAFTING_INIT},
    Stage.RESEARCH_MINOR_REVISION: {Stage.TASKED},  # re-Tasker
    Stage.RESEARCH_FULL_REVISION: {Stage.CLARIFIED},  # back to clarified with feedback
    Stage.RESEARCH_REJECTED: {Stage.BRAINSTORMED},
    # Paper Spec Kit pipeline (US4):
    Stage.PAPER_DRAFTING_INIT: {Stage.PAPER_SPECIFIED},
    Stage.PAPER_SPECIFIED: {Stage.PAPER_CLARIFIED},
    Stage.PAPER_CLARIFIED: {Stage.PAPER_PLANNED},
    Stage.PAPER_PLANNED: {Stage.PAPER_TASKED},
    Stage.PAPER_TASKED: {Stage.PAPER_ANALYZED},
    Stage.PAPER_ANALYZED: {Stage.PAPER_IN_PROGRESS},
    Stage.PAPER_IN_PROGRESS: {Stage.PAPER_COMPLETE, Stage.PAPER_IN_PROGRESS},
    # paper_complete is now a brief checkpoint where the 12 paper
    # specialists run before paper_review.
    Stage.PAPER_COMPLETE: {
        Stage.PAPER_REVIEW,
        Stage.PAPER_ACCEPTED,
        Stage.PAPER_MINOR_REVISION,
        Stage.PAPER_MAJOR_REVISION_WRITING,
        Stage.PAPER_MAJOR_REVISION_SCIENCE,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
    },
    # Final paper review (US5).
    #
    # Spec 012 adds three new outgoing transitions from PAPER_REVIEW to
    # support the convergence pipeline:
    #   - BRAINSTORMED (direct reject when any action item has severity=fatal)
    #   - PAPER_REVISION_IN_PROGRESS (auto-plan kicks off for writing/science)
    # The old direct transitions (PAPER_MINOR_REVISION / WRITING / SCIENCE /
    # FUNDAMENTAL_FLAWS) remain valid for back-compat with deployments that
    # don't yet have the auto-plan revision pipeline wired up.
    Stage.PAPER_REVIEW: {
        Stage.PAPER_ACCEPTED,
        Stage.PAPER_MINOR_REVISION,
        Stage.PAPER_MAJOR_REVISION_WRITING,
        Stage.PAPER_MAJOR_REVISION_SCIENCE,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
        Stage.PAPER_REVISION_IN_PROGRESS,
        Stage.BRAINSTORMED,
    },
    Stage.PAPER_ACCEPTED: {Stage.POSTED},
    Stage.PAPER_MINOR_REVISION: {Stage.PAPER_TASKED},
    Stage.PAPER_MAJOR_REVISION_WRITING: {Stage.PAPER_CLARIFIED},
    Stage.PAPER_MAJOR_REVISION_SCIENCE: {Stage.CLARIFIED},  # back to research clarify
    Stage.PAPER_FUNDAMENTAL_FLAWS: {Stage.BRAINSTORMED},
    # Convergence-pipeline stages (spec 012):
    Stage.PAPER_REVISION_IN_PROGRESS: {
        Stage.READY_FOR_IMPLEMENTATION,
        Stage.PAPER_REVISION_BLOCKED,
    },
    Stage.READY_FOR_IMPLEMENTATION: {Stage.PAPER_REVIEW},
    Stage.PAPER_REVISION_BLOCKED: {
        Stage.PAPER_REVIEW,
        Stage.PAPER_MINOR_REVISION,
        Stage.BRAINSTORMED,
    },
    Stage.POSTED: set(),  # terminal
    Stage.HUMAN_INPUT_NEEDED: set(),  # exit only via human action
    Stage.BLOCKED: set(),
}


def is_valid_transition(src: Stage, dst: Stage) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def successors(src: Stage) -> set[Stage]:
    return ALLOWED_TRANSITIONS.get(src, set())


def all_stages() -> Iterable[Stage]:
    return Stage


__all__ = ["ALLOWED_TRANSITIONS", "is_valid_transition", "successors", "all_stages"]
