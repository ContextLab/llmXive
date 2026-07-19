# Issue #1242 — Slice 6 COMPLETE (2026-07-18) — execution-tier ladder → typed escalating constraints

## ✅ SLICE 6 DONE — final whole-branch review READY-TO-MERGE — NOT pushed

Branch `026-model-selection-consolidation`. Slice 6 migrated the hardcoded execution-tier
**model-id** ladder (`FREE_MODEL_TIERS`) into typed, composable, **escalating `RequirementOverrides`
constraints** resolved through the unified `route_chat`/`select` chokepoint, threaded end-to-end
(graph dispatch → speckit context → convergence panel/reviser → model layer), plus a `require_paid`
cost-class field so a paid escalation rung genuinely reaches a paid model.

Built subagent-driven (implementer + spec/quality reviewer per task; opus final review). Full
offline suite **6939 passed / 17 skipped / 0 failed** (`tests/unit tests/contract tests/integration
-m "not slow"`); ruff clean on all 35 changed files; `git diff --check` clean; migration manifest
current (frozen-drift test green). Design + plan committed under `notes/2026-07-18-issue-1242-slice6-{design,plan}.md`.

**Post-final-review fix (maintainer 2026-07-18, Low):** `record()` + `record_offload()` re-read prior
`fix_rounds`/`model_tier` with a bool-permissive `isinstance(x, int)` and wrote them back (a corrupt
`"model_tier": true` → rewritten tier 1; `"fix_rounds": true` → 2 on next failure), partially defeating
the read-path bool-safety fix. Both write paths now route through `_nonneg_int` + a read→record→read
regression test (`test_record_bool_safety_read_write_cycle`). Commit `efc5dba55d`. Maintainer verdict:
"After replacing those two conversions … I'd consider Slice 6 ready." → **DONE, Slice 6 READY.**

### Commit stack (base = Slice-6 start `447ba83824`; re-fetch + rebase onto origin/main BEFORE any PR — local main lags ~785 commits)
```
efc5dba55d fix(026 Slice-6): bool-safe counters on the record() write path too              (post-review)
4f040256af docs(026 Slice-6): FR-003 require_paid + US6/SC-007 migration delta + per-tier golden   (Task 8)
c415188066 feat(026 Slice-6): graph dispatch threads tier overrides into SlashCommandContext        (Task 7)
276872f0ad feat(026 Slice-6): thread requirement_overrides through speckit + convergence panel       (Task 6)
fc9ae88ea1 feat(026 Slice-6): thread RequirementOverrides through the router walkers                 (Task 5)
7147cf8f06 feat(026 Slice-6): execution-tier ladder on TierConstraint (no model-id literals)         (Task 4)
3bbb0809c9 feat(026 Slice-6): canonical fresh_paid_headroom_available() (Constitution I)             (Task 3)
59f2d0826d feat(026 Slice-6): typed RequirementOverrides + route_chat precedence & compose-merge     (Task 2)
408a02d3e0 feat(026 Slice-6): require_paid cost-class field + select free-exclusion gate             (Task 1)
```
(+ the `447ba83824` plan-doc commit and the two design-doc commits `df49260c76`/`ed6f9e5771` below it.)

## What changed (the mechanism)

- **`ModelRequirement.require_paid: bool`** (`types.py`) + a one-line gate in `select.py`
  (`if requirement.require_paid and is_free: continue`) — a require_paid rung excludes ALL free
  candidates so paid genuinely leads; `require_paid ∧ ¬allow_paid` fails closed with `ModelUnavailable`.
- **`RequirementOverrides`** frozen dataclass (`allow_paid|None`, `require_paid`, `exclude_models`,
  `max_credits`). `route_chat` gained an `overrides=` param with (a) `allow_paid` precedence — BOTH
  standalone param + `overrides.allow_paid` non-None → `ValueError`; else overrides→param→snapshot; and
  (b) a COMPOSE-with-base-profile merge (union `exclude_models`, tighter `max_credits`, OR `require_paid`)
  — never replaces profile-owned fields. The old `**requirement_overrides` catch-all was removed.
- **`execution_status.py`** ladder rebuilt on `TierConstraint` (`allow_paid`, `exclude_registered_default`,
  `require_paid`, `.is_paid`, `.to_overrides(default_model)`): tier 0 = free (allow_paid=False);
  tier 1 = free second-opinion (exclude the registered default → policy's next-best free = gemma-4);
  tier 2 = single paid rung (allow_paid=True, require_paid=True), only when enabled. `tier_overrides()`/
  `tier_constraint()` replace `execution_model_override`/`tier_model`; corrupt/out-of-range tier →
  tier-0 free-only (via `_nonneg_int`, bool-safe) — NEVER the paid rung. `paid_tier_usable()` (no arg)
  DELEGATES to the new canonical `backends/credits.fresh_paid_headroom_available()` (Constitution I —
  all headroom arithmetic lives in credits.py). Config: `LLMXIVE_EXECUTION_PAID_ESCALATION` (bool);
  legacy `LLMXIVE_EXECUTION_PAID_TIERS` deprecated (nonempty → one rung + one-time warning; model-ids ignored).
  `model_tier`/`fix_rounds` bool-safety fixed (`_nonneg_int`).
- **Threading**: router walkers (4) → `overrides=`; `SlashCommandContext.requirement_overrides` →
  `run()`/`chat_with_fallback`; `build_*_reviewspec` → `_wire_live_panel`/`build_panel` → `LLMReviewer`
  (self._overrides) → `chat_with_model_fallback`; reviser **declared** `_overrides` field on all 7
  reviser classes → `invoke_reviser_backend` → `reasoning_chat`. All `RequirementOverrides` imports
  are `TYPE_CHECKING`-only where they'd cycle (`model_selection __init__ → execute → router`).
  Research-tasks bridge (`_tasker_engine_bridge.run_tasker_via_engine`) threads it from `tasks_cmd`'s ctx.
- **graph dispatch** computes `tier_overrides(project.id, default_model=entry.default_model)` for the
  escalation-bearing paths (`_exec_fix = implementer ∧ IN_PROGRESS`; `_panel_stage ∈ _STAGE_PANEL_LABEL`,
  which includes the paper doc-stage panels) and sets `ctx.requirement_overrides`. `default_model` stays
  the registry default (per-agent base profiles = Slice 7).
- **spec.md**: FR-003 gains `require_paid`; US6/SC-007 record the sanctioned tier-1 gpt-oss→gemma-4 delta
  + the `LLMXIVE_EXECUTION_PAID_ESCALATION` config. Backed by a real per-tier golden
  (`test_execution_tier1_golden_leads_with_gemma4`, `test_execution_tier2_golden_is_paid_only_leader_claude`).

## Sanctioned behavior deltas (record in the PR/merge notes)
1. **tier-1 free second-opinion**: `openai.gpt-oss-120b` (pinned) → `google.gemma-4-31B-it`
   (policy-selected next-best free after excluding the registered default). Maintainer-approved; the
   point of "not another list of model ids."
2. **tier-0 exec-fix/panel dispatch is now free-only** (`allow_paid=False`) even under global
   `LLMXIVE_PAID_OPT_IN=1` — vs. snapshot-derived (paid-fallback-eligible) pre-Slice-6. This is the
   maintainer's own **round-1 blocking fix #1** ("tier 0 can accidentally allow paid execution" → free
   rungs must emit `allow_paid=False`). Strictly spend-TIGHTENING (fail-closed, never broadening), a
   no-op in the default opt-in-off config, and selection-identical today (all registry agents are free).

## Open follow-up (NOT a Slice-6 blocker — final review + maintainer-boundary confirmed)
- **Paper exec-fix loop model-tier ladder**: the `paper_implementer` @ `PAPER_IN_PROGRESS` loop has no
  `bump_model_tier` (never had one) and so is not in the dispatch's escalation-bearing condition — a
  pre-existing boundary, faithfully preserved (paper DOC-stage panels ARE covered via `_STAGE_PANEL_LABEL`).
  File a follow-up to decide whether the paper exec-fix loop should gain the research loop's escalation
  ladder — a later-slice design call, contradicts Slice-6's behavior-preserving mandate to add now.

## Accumulated Minors (all KEEP per final review — nice-to-haves, not merge-blocking)
- Task 2: no explicit test for the `overrides=None` + standalone `allow_paid=` precedence branch (case c;
  unchanged carry-over). Optional one-liner.
- Task 3: a defensive non-finite cap/headroom recheck is unreachable (belt-and-suspenders, harmless).
- Task 5: no dedicated forwarding test for `chat_with_model_fallback`/`_walker_route` (share the tested
  `reasoning_chat`/`_walker_route` body; exercised via the reviewer-concurrency path).
- Task 6: 7 reviser files repeat the `_overrides` field (justified — mirrors per-reviser `_model`; a
  shared base is a bigger out-of-slice refactor).

## Remaining before a PR (user's call — do NOT push/PR without asking)
1. Re-fetch + **rebase onto origin/main** (local main lags ~655 commits; pipeline crons commit constantly).
   Expect the 2 pre-existing `web_data` dashboard-drift failures to resolve on rebase (they reference none
   of our modules).
2. **SC-008 real-call verification** (needs `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`): confirm a
   tier-2 requirement routes to a paid candidate with opt-in ON; `paid_tier_usable()` False / `next_usable_tier(1)`
   None with opt-in OFF. (Skipped offline.)
3. Optionally land the Task-2 one-line precedence test before merge.

## RESUME AT (next work)
- PR/merge decision for Slice 6 (after rebase) — MAINTAINER's call.
- **Slice 7**: per-agent requirement PROFILES via the `AgentRegistryEntry` schema migration (lands US5's
  schema-dependent ACs: AC1 all-agents fixed-snapshot primary preservation + AC4 `test_config_consistency`
  → capability profiles); the ~137 slice-7 manifest rows.
- **Slice 8**: `enforcement.py` static test + DELETE `MODEL_FALLBACKS`/`DEFAULT_MODEL`/`PAID_FALLBACK_MODELS`
  + the deprecated `LLMXIVE_EXECUTION_PAID_TIERS` shim.
- SDD artifacts (briefs, per-task reports, reviews, final-review, ledger) are under `.superpowers/sdd/`
  (git-ignored scratch).
