# Spec 023 (pipeline-e2e-completion) — execution log

Branch: `023-pipeline-e2e-completion`. Speckit pipeline: plan 6affd2cb →
tasks 2400249a → analyze fixes 2324278b (5 findings, clean on re-run) →
implementation in progress.

## T001 — baseline (2026-06-10)

`pytest tests/unit tests/contract tests/integration -q` on the feature
branch (post-T002/T003): **2355 passed, 16 skipped, 0 failed** (17:48).
No pre-existing failures; any later red is feature-caused.

## Phase 2 (T002/T003) — commit 9d3eb1ef

All 11 lane workflows now stage `specs/` (revision work-specs were
previously silently lost — FR-003).
`tests/unit/test_workflow_persist_paths.py` guards it; negative-verified
(pre-fix workflows fail 8/8).

## US1 (T004–T008) — commit cd1e103e

- graph.run_one_step persists advancement.evaluate's FULL result for
  review stages (the #303 discard bug); passthrough branch saves too.
- Coverage-gated reviewer dispatch via new `advancement.verdict_coverage`
  + `live_artifact_hash` (true artifact hash; shared
  `state.project.feature_dir_for` with both reviewers).
- `llmxive_implementer` (registered since spec 013, dispatched by NOTHING
  until now) is wired: unconsumed `revision_spec_path` → implementer, not
  reviewers (FR-002).
- New bounded revision cap `MAX_REVISION_ROUNDS = 3` → honest terminal
  (PAPER_FUNDAMENTAL_FLAWS / RESEARCH_FULL_REVISION).
- 12 new regression tests green; integration suites green.

## Encountered-issue ledger (FR-012)

| # | Found while | Issue | Fix |
|-|-|-|-|
| 1 | T004 design | `llmxive_implementer` registered but never dispatched anywhere (third severed link beyond the two in issue #303) | wired into graph dispatch + regression test |
| 2 | T004 design | auto-revision rounds were UNBOUNDED (round-N+1 forever; only the zero-success failsafe bounded anything) | MAX_REVISION_ROUNDS=3 → honest terminal, tested |
| 3 | T006 design | `_infer_live_hash` cannot detect post-review artifact changes (stale-verdict edge case) — it infers "live" from the records themselves | true-hash `live_artifact_hash` + shared `feature_dir_for`; coverage check uses it |

## T009 — real-state demonstration (pending)
