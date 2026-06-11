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

## T009 — real-state demonstration (US1)

Pass 1 (run 2f5c46df) on PROJ-565 (paper_review, complete current
12-specialist verdict set): ZERO reviewer dispatches (FR-004), evaluation
ran, and for the first time ever the decision PERSISTED —
`revision_spec_path = specs/auto-revisions/PROJ-565.../round-1` with a
23-task work-spec on disk. Pass 2 (implementer consumption, ~23 real LLM
calls + compile gates) running in background.

## US4 — T018 escalation-writer inventory (FR-015/017)

| Writer | Path | Classification | Action |
|-|-|-|-|
| flesh-out scope rejection | graph.py `_decide_next_stage` | (a) automated | FR-014: archive + constrained re-brainstorm via `process_scope_rejection`, bounded `IDEA_RETRY_CAP=3` → `VALIDATOR_REJECTED` terminal |
| validator idea rejection | graph.py sentinel branch | (a) automated | same bounded counter (was an unbounded reject→regenerate loop) |
| stage-panel engine failure | `_stage_panel.run_stage_panel` generic except | (a) automated | FR-016: deduped GitHub issue (`state/escalations.file_engine_failure_issue`); project stays at stage, schedulable (graph handler returns unchanged) |
| stage-panel outage paths | BackendUnavailable / TransientBackendError re-raise | already clean (PR #302) | regression-tested: no marker/issue/record |
| convergence kickback cap | graph.py `decision.escalate` | (b) bounded-with-evidence | exhaustion `EscalationRecord` (count/cap/concerns) written alongside the marker |
| clarifier attempt cap | `_clarify_attempts.write_human_input_needed` (clarify + paper_clarify) | (b) bounded-with-evidence | record written with rounds/cap; the LLM `escalate` verdict no longer parks below the cap (was unbounded!) |
| implementer UNKNOWN failsafe | implementer.py → AGENT_BLOCKED | (b) bounded-with-evidence | record with 3-zero-round evidence |
| publication sign-off | `awaiting_publication_signoff` | (c) sanctioned | US5 gate (maintainer vote) |

Digest: `state/escalations.update_digest` aggregates open records into ONE
issue; wired into llmxive-pipeline.yml (audit.yml was the analyze-stage
choice but is push/PR-triggered with contents:read — the 3h scheduled lane
has issues:write, so the digest lives there; tasks.md T020 note updated).

## US5 (T023–T029) — commit 79d5dbcf

`integrations/signoff_gate.py` (issue open → vote parse → idempotent
execute → remind), `project signoff-poll` CLI, `signoff-poll.yml` lane
(2h), `awaiting_publication_signoff` now `_NEVER_PICK`, AWAITING →
PAPER_REVIEW rejection transition, publisher idempotence (publication.yaml
convergence + `.zenodo_draft.yaml` resume ledger +
`ZenodoClient.get_deposition`). 14 regression tests. Encountered-issue
ledger #4: `zenodo_id=draft.deposition_id` crashed on the resume path
(draft None) → `published.deposition_id`.

## US6 (T035–T039) — commit 72036748

`state/paper_status.py` + wiring (compile script, pdf auditor,
paper-compile lane persist), bounded repair loop via the US1 revision
machinery, web_data `paper_status` (fail-closed "unverified"). Backfill
over the real shelf: **95 records — 76 restyled_unaudited, 19 fallbacks
now MARKED with reconstructed reasons (was 18+ silent)**. Full rendering
audit sweep over restyled PDFs running.

## US4 — T022 re-processing (FR-018)

PROJ-545 / PROJ-553 / PROJ-557 (parked pre-023 at human_input_needed with
kept `scope_rejected.yaml` markers) re-processed through the REAL
`process_scope_rejection` helper: each archived idea pulled from
`.archive/` into the constrained feedback, marker consumed, counter 1/3,
stage → brainstormed, escalation reason cleared.

**VERIFIED LIVE**: PROJ-545's constrained re-brainstorm ran for real — the
infeasible eye-tracking/human-subjects idea regenerated as a
GitHub-Actions-feasible computational study (aDDM on existing
moral-dilemma datasets) and advanced `brainstormed → flesh_out_complete`
with zero human input. The remaining two follow via the scheduled lanes.

## T030 — REAL sign-off round-trip (SC-006) ✅

Approval leg: synthetic gate-ready paper (PROJ-998, real lualatex PDF) →
issue **#304** opened (maintainer-tagged via `LLMXIVE_MAINTAINERS`
override so only @jeremymanning was pinged) → real 👍 reaction → publisher
minted **sandbox DOI 10.5072/zenodo.512176** → `posted` → issue closed
with the DOI. The first two publisher attempts FAILED on test-source tex
errors and the retry RESUMED the same deposition (512176) via the
`.zenodo_draft.yaml` ledger — the FR-020 no-double-mint path verified
against the real Zenodo sandbox.

Rejection leg: PROJ-997 → issue **#305** → real `reject: <reason>`
comment → parsed → reason landed verbatim in
`specs/auto-revisions/.../round-1/tasks.md`, project at `paper_review`
with `revision_spec_path` set → issue closed. Both synthetic projects
removed after the test (the closed issues are the durable evidence).

## T015 — negative control (FR-009) ✅

Four REAL validation passes over the live queue: PROJ-042, PROJ-546,
PROJ-582 honestly kicked back (`validator_revise` →
flesh_out_in_progress); PROJ-069 validated. No rubber-stamping.

## T039 — shelf sweep results (SC-007)

95/95 served papers carry records: **47 audited (pass), 29
restyled_unaudited (defects → repair work-specs generated), 19
fallback_original (every one now carries its reconstructed failure
reason)**. Zero unmarked fallbacks.

## US3 — PROJ-552 traversal status

Designated demo at `clarified` (reconciliation dispatch 27315363219
converged the clarify panel after the earlier honest 13-concern
methodology kickback; kickback trail on record, cap 1/3). Plan-stage pass
dispatched locally; subsequent stages run on the merged code via the
scheduled lanes (multi-day monitoring per the spec assumption). The
sign-off real round-trip (T030) and SC-001 complete when it reaches the
gate.
