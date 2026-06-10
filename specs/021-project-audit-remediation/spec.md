# Spec 021 — Project-Audit Remediation (issue #294)

**Status**: Implemented
**Input**: GitHub issue #294 "Project Audit, Tooling Landscape, and an
Actionable Engineering Plan" (2026-06-10), cross-referencing #112, #216,
#256, #263.

## Problem

The #294 audit found the pipeline bottlenecked by reliability at the
seams rather than by design. Verified against the live repo, four of its
findings were real and actionable:

1. **Canonical-truth contradictions (Constitution I violations).** A
   stale `pipeline_config.yaml` (paid GPT-4/Claude/Gemini models +
   numeric review-score gates, 2025-07-09) and a parallel JS-era
   orchestration layer (`src/core/*.js` with `review_points_threshold:
   5`, `scripts/*.js`, root `package.json`) contradicted the live
   Constitution (free-first models; convergence gate with **no** point
   system). Abolished "points threshold" prose was still being emitted
   into the public website by `src/llmxive/web_data.py`, and README/site
   prose named a fast model ("Gemma 3 27B") that disagreed with the
   registry single source of truth (`google.gemma-4-31B-it`).
2. **Non-deterministic librarian relevance judge (issue #112).**
   `judge_one()` pinned no temperature and the module's claimed verdict
   caching did not exist, so the same (question, candidate) flipped
   yes/no across runs — directly violating the librarian's SC-012
   reproducibility requirement.
3. **Validation gap at the LLM boundary.** Agent output validation was
   detect-and-die: run-log 2026-06-05..08 shows every
   `google.gemma-4-31B-it` fallback reviewer call failing fatally with
   "response missing YAML frontmatter", with no retry. The audit's
   Instructor-style remedy (feed the validation error back and re-ask)
   existed nowhere on the `Agent.run` path.
4. **No regression gate for prompts (issue #216).** Nothing prevented a
   prompt edit from silently breaking the output contract or destabilizing
   verdicts on the free models the pipeline depends on.

The audit's claim-verification asks (#256) were verified as **already
implemented** by specs 016–020 (claims register→resolve→cache,
result receipts, triples, semantic substantiation) and required no new
work beyond real-call validation.

## Functional requirements

- **FR-001**: The repo MUST contain exactly one model/agent configuration
  source of truth (`agents/registry.yaml`); the legacy
  `pipeline_config.yaml`/`pipeline_schema.json` and the orphaned JS-era
  layer MUST be deleted (zero live references verified before removal).
- **FR-002**: No live code or user-facing text may emit point-system
  language ("points threshold", "Human reviews count double",
  `review_points_threshold`); stage descriptions MUST describe the
  spec-015 convergence gate.
- **FR-003**: User-facing model prose (README, website About) MUST name
  the registry's actual models verbatim so prose cannot drift from config.
- **FR-004**: A `test_config_consistency` suite MUST pin FR-001..003:
  free-models-only registry (absent explicit `paid_opt_in`), fallback
  chains free and complete, legacy configs absent, banned phrases absent,
  README↔registry model agreement.
- **FR-005** (#112): The relevance judge MUST run at temperature 0.0 and
  freeze each non-fail-open verdict in a per-verdict disk cache keyed by
  (normalized query, candidate primary pointer, prompt-content hash);
  replays MUST return the frozen verdict without an LLM call. Fail-open
  verdicts (backend unreachable / unparseable) MUST NOT be cached.
- **FR-006**: The local transformers backend MUST honor `temperature=0`
  as deterministic greedy decoding (the prior `temperature or 0.7`
  silently discarded it) and MUST use the tokenizer's chat template when
  one exists.
- **FR-007**: `Agent.run` MUST retry on `MalformedResponseError` from
  `handle_response`, re-prompting with the concrete validation error and
  a contract-specific format reminder, bounded at
  `MAX_MALFORMED_RESPONSE_RETRIES` (= 2) re-asks (Constitution V: bounded,
  fail-fast). Research/paper reviewers MUST raise typed
  `MalformedResponseError` (frontmatter regex, YAML parse, mapping shape,
  `ReviewRecord` schema) instead of bare `RuntimeError`.
- **FR-008**: A prompt-regression eval gate MUST run on PRs touching
  `agents/prompts/**`, validating responses with the PRODUCTION parser
  (not a parallel re-implementation) across repeated runs, via the
  production backend router.

## Success criteria

- **SC-001**: Full offline suite (unit + contract + integration) passes,
  including the new guard/retry/judge suites.
- **SC-002**: Real-call (no mocks) validation: 3 consecutive
  `judge_one()` calls on the verbatim PROJ-261 question return identical
  verdicts through a real model; a second call replays `cached=True`
  from disk (`tests/real_call/test_relevance_judge_real.py`).
- **SC-003**: The audit's stale-state claims are either fixed here or
  explicitly recorded as already-superseded (issue #294 close-out
  comment maps every audit item to its disposition).

## Explicitly out of scope (filed as follow-ups, not silently dropped)

- DSPy prompt optimization for small models (#216): requires a labeled
  eval set that does not exist yet.
- Orchestration-harness pilot (LangGraph/Deep Agents/smolagents) and the
  per-project repo split (#263): Phase 3 of the audit, marked optional
  there; needs a maintainer scope decision.
- Adding `instructor` as a dependency was **rejected** (not deferred):
  routing through it would bypass the router's free-model guard, per-model
  circuit breakers, and peer-model fallback. The retry-with-feedback
  pattern was implemented inside the existing boundary instead (FR-007).
