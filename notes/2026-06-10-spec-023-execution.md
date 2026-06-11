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

## T043 — Success-criteria evidence (as of 2026-06-11)

| SC | Status | Evidence |
|-|-|-|
| SC-001 | IN PROGRESS (wall-clock) | PROJ-552 at plan stage with full kickback/recovery history in `state/projects/PROJ-552-*.history.jsonl`; remaining phases run on the merged lanes; sign-off machinery proven by SC-006 |
| SC-002 | MET (first exits ever) | PROJ-565: first persisted review decision (`revision_spec_path` survives the pass, run 2f5c46df); cap-terminal + accept paths regression-tested (test_graph_advancement_persistence) |
| SC-003 | MACHINERY LANDED | validate-ideas lane (hourly, drain ~192/day > intake) + intake throttle live; real drain observed: 4 validations → 1 validated + 3 honest kickbacks; trend measured over the post-merge window |
| SC-004 | MET | complete+current verdict set → ZERO reviewer dispatches (test_review_dispatch_gating + real PROJ-565 pass made no reviewer calls); stale → only stale specialists |
| SC-005 | MET (writers) | every surviving escalation writer validates rounds>=bound at write time (tests/contract/test_escalation_record); infra failures produce nothing; 3 parked projects de-escalated, PROJ-545 verified through to flesh_out_complete |
| SC-006 | MET | real round-trip: issue #304 → 👍 → sandbox DOI 10.5072/zenodo.512176 → posted → issue closed; #305 reject → reason → revision loop |
| SC-007 | MET | 95/95 papers carry status records (47 audited / 29 defect-flagged w/ repair specs / 19 marked fallbacks); web_data fail-closed "unverified" for recordless PDFs |
| SC-008 | MET | final clean offline suite **2440 passed, 16 skipped, 0 failed**; real-call `-m "not slow"` **22 passed, 5 skipped, 0 failed** |

## Encountered-issue ledger (FR-012)

| # | Found while | Issue | Fix |
|-|-|-|-|
| 1 | T004 design | `llmxive_implementer` registered but never dispatched anywhere (third severed link beyond the two in issue #303) | wired into graph dispatch + regression test |
| 2 | T004 design | auto-revision rounds were UNBOUNDED (round-N+1 forever; only the zero-success failsafe bounded anything) | MAX_REVISION_ROUNDS=3 → honest terminal, tested |
| 3 | T006 design | `_infer_live_hash` cannot detect post-review artifact changes (stale-verdict edge case) — it infers "live" from the records themselves | true-hash `live_artifact_hash` + shared `feature_dir_for`; coverage check uses it |
| 4 | T026 test | publisher crashed on the resume path (`zenodo_id=draft.deposition_id` with draft None) | use `published.deposition_id` |
| 5 | T009 pass 2 | `implementer_edit.md` `{token}` placeholders never rendered (`substitute()` is `{{token}}`) — EVERY per-task edit prompt since spec 013 went out raw | placeholders converted; render regression test |
| 6 | T009 pass 2 | `_validate_edit_path` rejected project-relative paths (21/39 real edits discarded) | accepts project- and repo-relative, still project-fenced |
| 7 | T009 pass 2 | `_read_tasks_md` captured the adapter's `[REV]` tag as severity | only real severities count; `(severity: X)` parsed from text |
| 8 | Stage 5 | clarifier `escalate` verdict parked immediately (unbounded escalation writer) | bounded at the attempt cap + evidence record |
| 9 | Stage 5 | clarifier-cap escalation record wrote to env repo root in hermetic tests | `_repo_root_from(memory_dir)` |

## T009 — real-state demonstration (US1)

Pass 1 (run 2f5c46df) on PROJ-565 (paper_review, complete current
12-specialist verdict set): ZERO reviewer dispatches (FR-004), evaluation
ran, and for the first time ever the decision PERSISTED —
`revision_spec_path = specs/auto-revisions/PROJ-565.../round-1` with a
23-task work-spec on disk.

Pass 2 (implementer): the work-spec was CONSUMED correctly (spec cleared,
stage held at paper_review — FR-002 semantics verified on real state),
but all 39 tasks skipped — which surfaced **three latent defects, fixed
generally + regression-tested (commit f94061db, encountered-issue ledger
#5-7)**: (a) `implementer_edit.md` used `{token}` placeholders while
`substitute()` implements `{{token}}` — every per-task edit prompt since
spec 013 reached the LLM UNRENDERED; (b) `_validate_edit_path` rejected
project-relative paths (21/39 real edits discarded for this alone);
(c) `_read_tasks_md` took the adapter's `[REV]` tag as the severity.
Round-2 spec persisted by a fresh evaluation pass; the FIXED implementer
round is consuming it.

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
