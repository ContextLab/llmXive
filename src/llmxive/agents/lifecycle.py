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
    Stage.BRAINSTORMED: {Stage.FLESH_OUT_IN_PROGRESS},
    Stage.FLESH_OUT_IN_PROGRESS: {Stage.FLESH_OUT_COMPLETE, Stage.HUMAN_INPUT_NEEDED},
    Stage.FLESH_OUT_COMPLETE: {Stage.PROJECT_INITIALIZED},
    # Per-project research Spec Kit pipeline (US1):
    Stage.PROJECT_INITIALIZED: {Stage.SPECIFIED},
    Stage.SPECIFIED: {Stage.CLARIFY_IN_PROGRESS, Stage.HUMAN_INPUT_NEEDED},
    Stage.CLARIFY_IN_PROGRESS: {Stage.CLARIFIED, Stage.HUMAN_INPUT_NEEDED},
    Stage.CLARIFIED: {Stage.PLANNED},
    Stage.PLANNED: {Stage.TASKED},
    Stage.TASKED: {Stage.ANALYZE_IN_PROGRESS},
    Stage.ANALYZE_IN_PROGRESS: {Stage.ANALYZED, Stage.HUMAN_INPUT_NEEDED},
    Stage.ANALYZED: {Stage.IN_PROGRESS},
    Stage.IN_PROGRESS: {Stage.RESEARCH_COMPLETE, Stage.IN_PROGRESS},
    Stage.RESEARCH_COMPLETE: {Stage.RESEARCH_REVIEW},
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
    Stage.PAPER_COMPLETE: {Stage.PAPER_REVIEW},
    # Final paper review (US5):
    Stage.PAPER_REVIEW: {
        Stage.PAPER_ACCEPTED,
        Stage.PAPER_MINOR_REVISION,
        Stage.PAPER_MAJOR_REVISION_WRITING,
        Stage.PAPER_MAJOR_REVISION_SCIENCE,
        Stage.PAPER_FUNDAMENTAL_FLAWS,
    },
    Stage.PAPER_ACCEPTED: {Stage.POSTED},
    Stage.PAPER_MINOR_REVISION: {Stage.PAPER_TASKED},
    Stage.PAPER_MAJOR_REVISION_WRITING: {Stage.PAPER_CLARIFIED},
    Stage.PAPER_MAJOR_REVISION_SCIENCE: {Stage.CLARIFIED},  # back to research clarify
    Stage.PAPER_FUNDAMENTAL_FLAWS: {Stage.BRAINSTORMED},
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
