# Specification Quality Checklist: llmXive website — UI bug-fixes and polish

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-12
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)  — *NOTE: the spec names the existing site's substrate (`web/`, `docs/`, `web/data/projects.json`, `web_data.py`, `web/js/auth.js`, the `llmxive_gh_token` localStorage key, the Cloudflare-Worker OAuth proxy) and the `agents/registry.yaml` + `agents/prompts/` pattern for the new maintenance agent — because the feature IS "fix these specific bugs / add this affordance to this specific existing system." That's the substrate, not a premature tech choice. The FRs/SCs are behavior-level.*
- [x] Focused on user value and business needs  — a credible front door, a browsable dashboard, working sign-out + account switching, legible pipeline/registry, human submission of feedback/papers that actually gets processed, accurate docs
- [x] Written for non-technical stakeholders  — the user stories + acceptance scenarios are plain-language
- [x] All mandatory sections completed  — Overview, Clarifications, User Scenarios & Testing, Requirements, Key Entities, Success Criteria, Assumptions, Out of Scope

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain  — **6 clarifications resolved** (`## Clarifications` Session 2026-05-12): mobile tab indicator → same sliding underline made geometrically correct; Markdown rendering → client-side vendored lib; account-switching → revoke OAuth grant on sign-out via the Cloudflare proxy (fallback: force account-chooser); feedback/paper recording → tagged GitHub issues consumed by a new hourly-cron maintenance agent (supersedes the earlier `feedback/`-file answer); post-submission UX → modal shows "issue created (link); processed within the hour".
- [x] Requirements are testable and unambiguous  — FR-001..FR-021 each map to a concrete check; SC-001..SC-016 are measurable
- [x] Success criteria are measurable  — counts of misalignment cases, % of rows naming a model, 0 broken embeds, 100%-of-test-runs for sign-out, 100% of submissions show the issue-link-and-hour message, 100% of cron-processed issues acted-on-commented-closed, etc.
- [x] Success criteria are technology-agnostic  — *NOTE: SC-006 references the `llmxive_gh_token` storage key as the verifiable artifact for "sign-out cleared state"; unavoidable for an auth-state bug. No frameworks/languages.*
- [x] All acceptance scenarios are defined  — 4 for US1, 4 for US2, 4 for US3, 3 for US4, 5 for US5, 2 for US6
- [x] Edge cases are identified  — missing model attribution, unknown artifact type, OAuth-proxy down / revocation fails, proxy can't do revocation (→ fallback), step with no examples, failed issue creation, maintenance agent can't decide / LLM fails, overlapping cron runs, mobile modals, cron-regeneration regression
- [x] Scope is clearly bounded  — explicit "Out of Scope" section; the maintenance agent IS in scope but its job is bounded ("triage one issue → route/create/file/acknowledge → comment → close"); the Cloudflare "revoke grant" endpoint is the one in-scope hosting touch
- [x] Dependencies and assumptions identified  — the static-site layout, the Cloudflare OAuth proxy + its needed "revoke grant" endpoint (with fallback), the run-log model-attribution source, the existing pipeline-diagram, the vendored-Markdown-renderer choice, the agent-registry/prompts pattern for the new agent, the new hourly GitHub Action workflow

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria  — each FR traces to a US acceptance scenario and/or an SC
- [x] User scenarios cover primary flows  — clean dashboard (US1), browsable project modals (US2), working sign-out + account switching (US3), pipeline/registry exploration (US4), feedback/paper submission + hourly triage (US5), how-to-contribute + README (US6)
- [x] Feature meets measurable outcomes defined in Success Criteria  — SC-001..SC-016 are the acceptance bar
- [x] No implementation details leak into specification  — beyond the unavoidable naming of the existing system's substrate (see Content Quality notes)

## Notes

- This started as a pure website bug-fix spec; the `/speckit-clarify` pass on #115 item 8 pulled a **new lightweight maintenance agent + an hourly intake cron** into scope (the user's clarification made the backend small enough to fit). The spec now spans static-site fixes, data-correctness fixes (in `web_data.py`), an auth fix (client + a small Cloudflare-proxy adjunct), the submission front-end, and the maintenance-agent backend.
- Item 6 (sign-out) is flagged CRITICAL/SECURITY in #115 and is a P1 user story (US3) to be triaged first.
- All [NEEDS CLARIFICATION] markers resolved. Spec is ready for `/speckit-plan` (a further `/speckit-clarify` pass is optional — the open decisions are now settled).
