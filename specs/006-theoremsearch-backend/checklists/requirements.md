# Specification Quality Checklist: TheoremSearch backend for the librarian + mathematics as 9th default field

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-12
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)  — *NOTE: this spec necessarily names the TheoremSearch API (theoremsearch.com) and the librarian's existing arXiv client because the feature IS "integrate this specific external service into this specific existing agent." That's domain content, not premature implementation choice. No code structure, no class names, no language is prescribed.*
- [x] Focused on user value and business needs  — better math-paper recall; making math a first-class field
- [x] Written for non-technical stakeholders  — the user stories and acceptance scenarios are plain-language
- [x] All mandatory sections completed  — User Scenarios, Requirements, Success Criteria, Assumptions all present

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain  — **resolved at /speckit-clarify (Session 2026-05-12)**: (a) math-classifier cache key → per-project `(project_id, librarian_prompt_version)`; (b) classifier-error handling → loud stderr diagnostic + a `math_classifier` audit object in the LibrarianResult JSON. The FR-A10 seed-project-sequencing note was converted from a marker to a plain note (it's a /speckit-tasks ordering detail, not a spec-level decision).
- [x] Requirements are testable and unambiguous  — every FR maps to a concrete check; SCs are measurable
- [x] Success criteria are measurable  — SC-A01..A09 each state a verifiable condition
- [x] Success criteria are technology-agnostic  — *NOTE: SC-A01/A03 reference "arXiv ID" and "backend tag" because those are the verifiable artifacts the librarian's existing output contract uses; this is unavoidable for an amendment to an existing system. No frameworks/languages.*
- [x] All acceptance scenarios are defined  — 5 for US1, 4 for US2
- [x] Edge cases are identified  — 6 edge cases covering API failure, malformed IDs, classifier failure, false-positive triggers, dedup, and the empty-corpus skip
- [x] Scope is clearly bounded  — explicit "Out of Scope" section; Spec B (#114) carries the deferred parts
- [x] Dependencies and assumptions identified  — Assumptions section lists the TheoremSearch-API and existing-librarian-behavior dependencies; the "Decided" sub-list records maintainer answers from #111

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria  — FR-A01..A13 each trace to a US acceptance scenario or an SC
- [x] User scenarios cover primary flows  — math-field always-trigger, non-math classifier-gated trigger, non-arXiv skip, API-failure fall-through, dedup, the 9th-field addition, the seed projects, the cross-domain parametrization
- [x] Feature meets measurable outcomes defined in Success Criteria  — yes, SCs are the acceptance bar
- [x] No implementation details leak into specification  — beyond the unavoidable naming of the external service and the existing agent it amends (see Content Quality notes)

## Notes

- All [NEEDS CLARIFICATION] markers resolved at `/speckit-clarify` (Session 2026-05-12) — see the spec's `## Clarifications` section. Two questions asked + answered: (1) classifier cache key → per-project; (2) classifier-error handling → loud + recorded (`math_classifier` audit object — the one deliberate output-JSON addition in this amendment). The seed-project-sequencing item was downgraded from a marker to a plain FR-A10 note (it's a task-ordering detail for `/speckit-tasks`, not a spec decision).
- This is an **amendment to spec 005**, not a standalone spec. The spec dir is `specs/006-theoremsearch-backend/` for tooling convenience, but the deliverable modifies the spec-005 librarian + its diagnostic + its registry entry rather than standing up a new agent. FR-A13 captures the spec-005 doc updates.
- Maintainer answers from issue #111 (recorded in the "Decided" sub-list of Assumptions): amendment not new spec; keep + per-project-cache the classifier; add math as 9th field + brainstorm 5 seed projects; Spec A skips non-arXiv sources (Spec B keeps them with quality checks).
- `/speckit-analyze` (Session 2026-05-12) found 0 CRITICAL / 0 HIGH issues and 4 LOW findings, all fixed in the same session: (I1) FR-A12 now names the version target `1.5.0 → 1.6.0`; (A1) the math-classifier-failure edge case + SC-A02 + the `math_classifier` Key-Entity description now split "backend failure" (`{invoked:true, verdict:false, error:"<msg>"}` + loud stderr) from "unparseable-but-returned" (`{invoked:true, verdict:false, error:null}` + logged warning), matching `contracts/math-classifier.md`, and clarified that `verdict` is `null` *only* when `invoked` is `false`; (C1) the pre-existing two-copy field-list duplication is now tracked as hygiene follow-up GitHub issue #116 (referenced from plan.md, tasks.md, and `contracts/cross-domain-coverage-9fields.md`) — out of scope here, to be done after #113 lands; (U1) the conditional T030 (reference_validator `project_id` passthrough) was confirmed acceptable as-is (a documented branch with a documented fallback) — no edit needed.
- **Ready for `/speckit-implement`.**
