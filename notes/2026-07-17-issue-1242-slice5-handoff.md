# Issue #1242 — Session Handoff (2026-07-17→18) — Phase 2 Slice 5 ✅ APPROVED — RESUME AT SLICE 6

## ✅ M0 + SLICE 5 MAINTAINER-APPROVED (3 review rounds, no remaining findings) — next: Slice 6

**START HERE for a fresh session.** Slice 5 (all 3 legacy walkers retired; every registry/reasoning/
panel LLM call now flows `route_chat` → `select()` → `execute()`) is DONE, green, and **maintainer-
approved on 2026-07-18** — three review rounds resolved (architecture → paid-path F1–F4 → a lone
unused-noqa lint), verdict "M0 and Slice 5 remain approved and ready for Slice 6." Nothing pushed.

**Commit stack on base `b00d0b71c3`** (re-fetch + rebase onto origin/main BEFORE the PR — local main
lags; pipeline crons commit constantly): `5170772b61` M0 decision-A · `dc91dd24e1` route_chat
chokepoint · `85361c8edf` Step A (chat_with_fallback) · `3ce1e794b6` Step B (reasoning_chat +
chat_with_model_fallback retired) · `3e121792b4` review-2 paid-path fixes (F1–F4) · `c2f860743`
noqa cleanup (+ interspersed notes commits). Full non-slow backstop after the review fixes:
**6975 passed**, only the 2 PRE-EXISTING `web_data` dashboard-drift failures
(`test_web_data_blocks` / `test_web_data_contributors` — reference none of our modules; resolve on the
rebase). `git diff --check` clean; ruff clean on all session-changed src+test files (the 29 `tests/`
lints are identical on the base commit = pre-existing, outside the project's normal lint scope).

### ⏭️ SLICE 6 — execution-tier migration (the immediate next work)
Migrate `src/llmxive/state/execution_status.py` (`FREE_MODEL_TIERS` + `model_tier_ladder()` +
`paid_tier_usable()` + `execution_model_override` / `next_usable_tier`) and its `graph.py` consumers
ONTO the mechanism: escalating **requirement profiles / constraints** through `route_chat`/`select`
(same free→paid ordering: registered default → `openai.gpt-oss-120b` free → optional
`LLMXIVE_EXECUTION_PAID_TIERS` via the paid opt-in + credit guard). **Preserve** the `free_only`
fabrication guard + the persisted `model_tier`. Manifest slice-6 row: `execution_status.py` (was
`:63`, `FREE_MODEL_TIERS`; re-locate via the manifest — the file may have shifted). Regenerate the
manifest after any pin move (the frozen drift test enforces it). NOTE for Slice-6 tests: the autouse
`_offline_model_selection_snapshot` conftest fixture already makes `route_chat` deterministic offline
(free qwen→gemma-4→gpt-oss); paid-tier tests inject a paid-enabled snapshot + a tmp git `ledger_repo`
+ `LedgerConfig(remote=None)` (mirror `tests/integration/test_model_selection_execute.py`).

### Review-2 fixes (`3e121792b4`) — the guarded paid fallback is now functional end-to-end
The maintainer found the paid tail could never run through the new chokepoint. Fixed:
- **F1** `route_chat` defaulted `ledger_repo=None` → execute skipped every paid candidate. Now
  defaults to `repo_root()` (where the ledger ref is bootstrapped, `cli.py:358`); explicit param =
  test seam; still fails closed on an unbootstrapped anchor.
- **F2** `standard_generation` `max_candidates` 4→8: the composite snapshot has 4 free
  (qwen→gemma-4→gpt-oss→local qwen2.5) so free-before-paid truncated claude. Added an SC-007 golden
  on the FULL composite proving claude survives last.
- **F3** `LocalBackend` missing-runtime/checkpoint → `BackendUnavailable` (ADVANCE), not
  `PermanentBackendError` (which ABORTED the chain before paid). Unit + e2e integration test
  (`test_route_chat_reaches_paid_after_free_down_and_local_unavailable` — reservation opened→settling
  on a real git ledger).
- **F4** US5 delivery split made explicit+BINDING in spec.md (US5 + Delivery Slices) + plan.md
  (Slice 5/7): the schema-dependent US5 ACs (each agent expresses a profile; AC1 all-agents
  fixed-snapshot test; AC4 config_consistency→profiles) are deferred to **Slice 7** with the
  `AgentRegistryEntry` schema migration, and stay open.

**Remaining Slice-5 acceptance:** the 7 e2e tests (most covered by route/execute unit tests; the paid
e2e is now the integration test above) + SC-008 real-call verification (needs `DARTMOUTH_CHAT_API_KEY`).
Then Slice 6 (execution-tier ladder). US5 schema-dependent ACs are Slice 7 (see F4).

### How Step B worked (the autouse-stub approach the maintainer chose)
`reasoning_chat`/`chat_with_model_fallback` → thin wrappers over a shared `_walker_route` →
`route_chat`. The injected backend is adapted into a `backend_factory` (`lambda name: backend if
name == (backend.name or "dartmouth") else make_backend(name)`) — a fake with NO `.name` is treated
as the `dartmouth` serving backend. A new **autouse conftest fixture** (`tests/conftest.py`
`_offline_model_selection_snapshot`) stubs `route.runtime_snapshot` → a fixed free
qwen→gemma-4→gpt-oss snapshot + `reset_snapshot_cache()`, so injected-fake tests serve the primary
candidate deterministically offline. Result: the ~18-20 reviser/reviewer/claims test files passed
UNCHANGED. Retired `test_chat_with_model_fallback.py` + `test_model_fallback_outage_classification.py`
(peer-walk mechanics superseded by execute/router-primitive + `test_reasoning_walker_delegation.py`).

## 🟢 (historical) STATE: M0 decision-A + route_chat chokepoint + chat_with_fallback delegation DONE

Branch `026-model-selection-consolidation` (NOT pushed — re-fetch + rebase onto origin/main
before the PR). Base this session = `b00d0b71c3`. Read the prior handoff
[2026-07-16-issue-1242-handoff.md](2026-07-16-issue-1242-handoff.md) "POST-REVIEW STATE" for the
full corrected-Slice-5 spec + the 6 revert findings — this note is the delta on top of it.

### Two maintainer decisions RESOLVED this session (were open in the prior handoff)
- **(A) dartmouth tables split.** `_REASONING_MODELS` = **canonical** (backend serving-mode
  knowledge — thinking-mode disable + reasoning-safe budget; moving it to policy.py would create a
  `backends→model_selection` import cycle). `KNOWN_FREE_MODELS` = **migration_target** (live-catalog
  pricing + LKG supersede the hardcoded allowlist; delete in slice 8). Implemented as a symbol-level
  `_CANONICAL_SYMBOLS` sanction in inventory.py (dartmouth.py can't be wholly canonical).
- **(B) e2e #8** (`test_config_consistency` → capability profiles) lands in **Slice 7**, not
  corrected Slice 5 — spec AC §107 sits under US7; the test can't validate profiles until the
  registry schema carries them. So corrected Slice 5 carries **7** e2e tests, not 8.

### Commits this session (newest first) · base `b00d0b71c3`
- `5170772b61` M0 decision-A: sanction `_REASONING_MODELS` canonical-by-symbol + regen manifest
  (canonical 6→7, migration_target 142→141). Frozen drift test green.
- `dc91dd24e1` **route_chat chokepoint** (`model_selection/route.py`) — the corrected Slice-5 core
  (execute()-delegation). Widened `ExecutionOptions.temperature` → `float|None`.
- `85361c8edf` **chat_with_fallback → route_chat delegation** (Step A). Retired the superseded
  backend-name-chain tests in `test_model_fallback_outage_classification.py` (guarantee now asserted
  at the new seam, `test_chat_with_fallback_delegation.py`); added the LKG-usable route e2e (#5
  usable half); regenerated the manifest (test_double 330→337). Verified: a 179-test targeted run
  (new code + all at-risk chat_with_fallback consumers + the not-yet-rerouted walkers) is green; the
  ONLY real-body `chat_with_fallback` callers left are in `tests/real_call/` (skipped offline).

### What EXISTS + is correct (do NOT redo)
- **`model_selection/route.py:route_chat`** — the SINGLE chokepoint. Flow: guard no-llm sentinel →
  acquire REAL snapshot (bounded 30s **negative cache** `_acquire_snapshot`/`reset_snapshot_cache`;
  `_now`=monotonic, monkeypatchable) → derive `allow_paid` from `snap.credit.paid_opt_in` when None →
  `call_budget_for` → `build_requirement("standard_generation", …, allow_paid=…)` → pure `select` →
  `_promote_primary(chain, caller_model)` → `execute(chain, …, backend_factory, retries, ledger_*)`
  → `result.response`. NO string projection, NO legacy walker. `_promote_primary` moves whole
  Candidates (backend identity + pricing ride along) to front IFF select kept the caller's model;
  NEVER resurrects an absent one (revert-finding #3). Cold start → `ModelUnavailable` (fail closed).
  9 unit tests: `tests/unit/test_model_selection_route.py`.
- **`backends/router.py:chat_with_fallback`** now a THIN wrapper over route_chat (Step A): profile
  `standard_generation`, `caller_model=model`, `default_backend`/`fallback_backends` IGNORED
  (execute dispatches per-candidate `ModelRef.backend`), `max_tokens` default = GENERATION budget.
  **Outage-classification contract preserved:** `ModelUnavailable`/`ChainExhausted` → re-raised as
  `BackendUnavailable` (clean run-loop abort, never a human escalation); a request-level PERMANENT
  refusal propagates unchanged (execute() re-raises it). 5 tests:
  `tests/unit/test_chat_with_fallback_delegation.py`. All ~14 consumer test files that use
  chat_with_fallback MONKEYPATCH the symbol at their module import site → unaffected by the rewrite.

### Why Step A alone is a coherent Slice-5 increment
Slice 5's headline = "registry resolution + router DEFAULT_MODEL/MODEL_FALLBACKS consumers →
select()". `chat_with_fallback` IS the registry-agent path (`agents/base.py` reads the registry
entry → chat_with_fallback). Rerouting it = registry agents now resolve through select(). Kept the
diff small deliberately (the prior Slice 5 was reverted; smaller = reviewable).

## ⏭️ STEP B — retire `reasoning_chat` + `chat_with_model_fallback` (maintainer: "retire all 3 now")

**GROUND-TRUTH SCOPE (investigated 2026-07-18, before writing code — bigger than the earlier
estimate):** this is a SUBSYSTEM-WIDE migration, effectively the Slice-7 direct-pin consumer work.
- The injected backend flows into the walkers through TWO production seams that EVERY reviser/reviewer
  test drives: `convergence/revisers/_self_consistency.py:invoke_reviser_backend` (→
  `reasoning_chat(reviser._backend, …)`, used by every reviser) and
  `convergence/llm_reviewer.py:LLMReviewer._call_backend` (→
  `chat_with_model_fallback(self._backend, …)`). Plus the direct callers in
  claims/fill/grounding/triage/plan_cmd.
- **~18–20 test files break at once** the moment those walkers route through `route_chat`
  (which acquires a networked snapshot + uses `backend_factory`, ignoring the injected instance):
  `test_reviser_self_consistency`, `test_llm_reviewer_model_fallback`, `test_review_max_tokens_bound`,
  `test_llm_reviewer_yaml_recovery`, `test_review_r1_action_items_gate`, `test_concern_text_validation`,
  `test_convergence_review_cache`, `test_spec_kickback_inplace_revision`, `test_verified_facts_prompt`,
  `test_llm_reviewer_action_items_compat`, + integration `test_spec_reviser`, `test_paper_spec_reviser`,
  `test_llm_reviewer`, `test_panels_research`, `test_invariants`, `test_production_flags_active`,
  `test_tasker_*`. Plus `test_chat_with_model_fallback.py` (25) + the model-level half of
  `test_model_fallback_outage_classification.py` (RETIRE — superseded by execute/router-primitive).
- **No clean wrapper seam** keeps these green without touching them: the test fakes set the RESPONSE's
  `backend="dartmouth"` but do NOT give the fake object `.name="dartmouth"`, so threading
  `backend_factory = lambda name: injected if name==injected.name else make_backend(name)` sends the
  fake's candidates to the REAL Dartmouth backend (network). And `lambda name: injected` (fake serves
  every candidate) BREAKS production per-candidate dispatch (a local candidate would hit the Dartmouth
  backend — violates e2e #2/#4). So the injected-instance shape genuinely has to be migrated.
- **Two viable approaches (pick one):** (a) an autouse conftest fixture stubbing
  `route.runtime_snapshot` → a deterministic offline snapshot + `reset_snapshot_cache()`, PLUS give the
  test fakes `.name="dartmouth"` so threading works — WIDE blast radius, but few per-file edits; or
  (b) migrate each of the ~18 files to monkeypatch `_self_consistency.reasoning_chat` /
  `llm_reviewer.chat_with_model_fallback` (like the chat_with_fallback consumers already monkeypatch
  their walker symbol) — no production-code change, but ~18 mechanical test rewrites. Either is a
  dedicated focused effort (its own PR), NOT a tail-of-session add-on — do it fresh with the outage
  guarantee re-asserted at the wrapper level (as `test_chat_with_fallback_delegation.py` does).
  KEEP `chat_one_candidate`/`disposition_of` (execute's 1A primitive).
2. **Triage the superseded walker-mechanics tests** (confirmed RETIRE — execute()/router-primitive
   tests already cover the equivalents):
   - `tests/unit/test_chat_with_model_fallback.py` (25 tests: peer-walk vs MODEL_FALLBACKS +
     outage-class). Covered by `tests/unit/test_model_selection_execute.py`
     (`test_transient_advances_to_next_candidate`, `test_breaker_open_advances`,
     `test_permanent_refusal_aborts_and_does_not_advance`, `test_all_transient_raises_chain_exhausted`,
     `test_paid_guard_denial_skips_candidate`) + `test_model_selection_router_primitive.py`
     (chat_one_candidate retry/deadline/302). **Preserve the outage→BackendUnavailable-vs-BackendError
     aggregate assertions** at the wrapper level (a couple of new wrapper tests) before deleting.
   - `tests/unit/test_model_fallback_outage_classification.py` (5 direct calls) — same.
   - `tests/unit/test_llm_reviewer_model_fallback.py`, `tests/unit/test_reviser_self_consistency.py`
     — inspect how they inject (instance vs monkeypatch); migrate or retire.
   - `tests/unit/test_llm_call_centralization.py` = SAFE (static `.chat(` AST guard; route.py never
     calls `.chat` directly — delegates to execute→chat_one_candidate in router.py). No change.
3. **7 required e2e tests** (handoff §"REQUIRED e2e"; #8 deferred to slice 7 per decision B). Most
   behaviors already covered by route.py unit tests + execute integration; add the INTEGRATED-path
   ones: **#1** paid CREATES+SETTLES a reservation THROUGH route_chat on the real git-ledger (mirror
   `tests/integration/test_model_selection_execute.py` `repo`/`_exec` fixtures — route_chat passes
   `ledger_repo`/`ledger_config` straight through); **#5** LKG-in-bounds usable through route_chat
   (`catalog_source="last_known_good"` within `max_catalog_age_s` → succeeds). #2/#3/#4/#6/#7 have
   route-level coverage already; promote to explicit e2e if the maintainer wants.

## THEN Slices 6 → 7 → 8 — unchanged from the prior handoff
See [2026-07-16-issue-1242-handoff.md](2026-07-16-issue-1242-handoff.md): Slice 6 = execution-tier
ladder (`execution_status.py` `FREE_MODEL_TIERS`); Slice 7 = compat consumers + `AgentRegistryEntry`
schema + the 138 manifest slice-7 rows + e2e #8; Slice 8 = `enforcement.py` + DELETE
`MODEL_FALLBACKS`/`DEFAULT_MODEL`/`PAID_FALLBACK_MODELS`. Regenerate the manifest after every pin
move (frozen drift test enforces it). Still outstanding: SC-008 real-call verification (needs
`DARTMOUTH_CHAT_API_KEY`).

## Test commands + gotchas
```
.venv/bin/python -m pytest \
  tests/unit/test_model_selection_route.py tests/unit/test_chat_with_fallback_delegation.py \
  tests/unit/test_model_selection_inventory.py tests/unit/test_model_selection_execute.py \
  tests/unit/test_model_selection_select.py tests/unit/test_llm_call_centralization.py \
  tests/integration/test_model_selection_execute.py -q
.venv/bin/ruff check src/llmxive/model_selection/ src/llmxive/backends/router.py
```
- Prefix EVERY commit with `PRE_COMMIT_ALLOW_NO_CONFIG=1`; verify HEAD moved.
- route_chat is in `model_selection/`; the walkers in `backends/router.py` import it FUNCTION-LOCALLY
  (avoids the backends↔model_selection cycle — route.py imports router.make_backend at module level).
- Leave unrelated worktree noise alone: `projects/PROJ-317-…/docs/CONTRIBUTING.md` (M) +
  `notes/2026-07-15-issue-1139-audit-T+7min.md` (untracked) — NOT ours.
