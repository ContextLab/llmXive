# Specification Quality Checklist: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-06-04
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — requirements are stated as behavior/outcomes (skip kinds, frozen store, durable placeholder, references-verified), not code; domain concepts (DOI/arXiv, source hash, subject identity) are reused vocabulary from specs 016–019, not new implementation.
- [x] Focused on user value and business needs — unblock planning, eliminate waffling, keep accuracy paramount.
- [x] Written for the maintainer/technical stakeholder (consistent with specs 016–019, which are internal-pipeline specs).
- [x] All mandatory sections completed (User Scenarios, Requirements, Success Criteria; plus Context, Key Entities, Edge Cases, Assumptions).

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — the input was detailed enough to resolve scope; open design choices are recorded in Assumptions.
- [x] Requirements are testable and unambiguous (each FR maps to an acceptance scenario / success criterion).
- [x] Success criteria are measurable (zero kickbacks, same value across rounds, zero re-resolutions, zero cold re-resolutions).
- [x] Success criteria are technology-agnostic (outcome-focused; no frameworks/languages).
- [x] All acceptance scenarios are defined (Given/When/Then per user story).
- [x] Edge cases are identified (mixed ref+number, source change, distinct-subject non-collision, rendered view, scope-via-reference).
- [x] Scope is clearly bounded (planning vs. paper/implementation stages; Part A vs. Part B; reuse existing machinery).
- [x] Dependencies and assumptions identified (Assumptions section: stage classes, reference validator sufficiency, subject-identity key, source-hash invalidation).

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria (FR-001..016 trace to US1–US3 scenarios + SC-001..007).
- [x] User scenarios cover primary flows (references-only planning; frozen no-waffle cache; no-low-level-claims-in-docs).
- [x] Feature meets measurable outcomes defined in Success Criteria.
- [x] No implementation details leak into specification.

## Notes

- Two-part scope (A: planning references-only; B: deterministic frozen cache) is intentionally one spec because both govern the same claim layer; planning (Part A) sharply reduces the surface that Part B must protect, but Part B is independently required for the paper/research stages.
- Accuracy is **not** relaxed: references are still verified everywhere; Part B makes paper-stage verification *stronger* (deterministic + immutable). Only the *location* of low-level-claim verification changes (out of planning).
- `/speckit-clarify` COMPLETE (Session 2026-06-04) — all four design choices resolved: (1) planning = specify/clarify/plan/tasks; (2) verified store = tracked `state/claims/` keyed by subject_key (drop gitignored-cache dependence for freezing); (3) rendered view = render values from the frozen store at review time + final publish; (4) strip/smooth = LLM rewrite + re-detect guard + deterministic fallback. See spec `## Clarifications`.
