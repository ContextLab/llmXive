# Specification Quality Checklist: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-04
**Last Updated**: 2026-05-04 (refactored to use real projects + carry-forward gate)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [X] No implementation details (languages, frameworks, APIs)
  - Note: Spec references the existing `python -m llmxive run` orchestrator entry point as a constraint of the production code path (FR-001), not as an implementation choice. This is required by the user's explicit "use the actual pipeline code" directive.
- [X] Focused on user value and business needs
- [X] Written for non-technical stakeholders
  - Note: Audience is a pipeline maintainer (technical), but each user story leads with value (quality bar reached, ideas carried forward, defects fixed-or-deferred) before any technical detail.
- [X] All mandatory sections completed (User Scenarios & Testing, Requirements, Success Criteria)

## Requirement Completeness

- [X] No [NEEDS CLARIFICATION] markers remain
- [X] Requirements are testable and unambiguous
- [X] Success criteria are measurable
- [X] Success criteria are technology-agnostic (no implementation details)
- [X] All acceptance scenarios are defined (each of US1-US5 has Given/When/Then scenarios)
- [X] Edge cases are identified (backend down, empty artifacts, hallucinated citations, idempotent re-runs, iteration unbounded loop, weak pool, cross-iteration contamination, downstream failures, run-log gaps, quote-size cap)
- [X] Scope is clearly bounded — Phase 1 only, three agents (`brainstorm`, `flesh_out`, `idea_selector`), no Spec Kit scaffold, no paper-side pass; carry-forward gate explicitly hands off to spec 004
- [X] Dependencies and assumptions identified (Dartmouth Chat reachable, orchestrator CLI is the entry point, prompts/registry are editable, real projects committed, iteration capped at 5 cycles per agent, etc.)

## Feature Readiness

- [X] All functional requirements have clear acceptance criteria — each FR-### either gates a US### scenario or maps directly to one of issues #59/#60/#61
- [X] User scenarios cover primary flows (brainstorm pool grown to bar, flesh_out iterated to bar, idea_selector iterated to bar, verbatim report, carry-forward gate)
- [X] Feature meets measurable outcomes defined in Success Criteria (SC-001 through SC-009)
- [X] No implementation details leak into specification
  - Note: File paths (`projects/<id>/idea/seed.md`, `state/projects/<id>.yaml`, `state/run-log/<YYYY-MM>/<run-id>.jsonl`) are unavoidable because they are the artifact contracts the agents already produce; this spec describes how to inspect/iterate on those artifacts, not how to implement them.

## Refactor-Specific Validation (2026-05-04 update)

- [X] Real projects approach: spec replaces `PROJ-TEST-PHASE1-<timestamp>` throwaway with real `PROJ-NNN-<slug>` projects committed to `projects/`
- [X] Iteration loop is bounded (≤5 fix-and-re-run cycles per agent per FR-005 / SC-008)
- [X] Carry-forward gate is concrete (FR-017 names `carry-forward.yaml`, US5 defines its contents, SC-009 makes it a success criterion)
- [X] Sequential constraint preserved (FR-001: agents run one-at-a-time via `--max-tasks 1`)
- [X] Real API calls preserved (FR-002: no mocks, distinguishes transient backend failure from agent defect)
- [X] Verbatim quoting preserved (FR-006, FR-007, FR-008 capture artifacts, state, run-log, and iteration diffs)

## Notes

- All checklist items pass after the refactor.
- The spec now has 5 user stories (vs. 3 before): adding US3 (idea_selector quality, was bundled inside US1) and US5 (carry-forward gate) made the agent-by-agent iteration loop explicit.
- Ready to proceed to `/speckit-plan`.
