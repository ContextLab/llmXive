# Issue #1242 — Session Handoff (2026-07-17) — Phase 2 Slice 5, Step A landed

## 🟢 STATE: M0 decision-A + route_chat chokepoint + chat_with_fallback delegation DONE

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

## ⏭️ STEP B — remaining corrected-Slice-5 work (next session)
1. **Retire `reasoning_chat` + `chat_with_model_fallback` as prod entry points** → thin route_chat
   wrappers (same pattern as chat_with_fallback; `standard_generation` provisional profile;
   preserve the outage-classification translation). These are the ~52 slice-7 compat consumers'
   current entry (claims/fill/grounding/convergence-revisers/llm_reviewer). They take a backend
   INSTANCE — the wrapper must adapt: cleanest is to DROP the instance (execute uses backend_factory
   per-candidate) and migrate the instance-injection tests. KEEP `chat_one_candidate`/
   `disposition_of` (execute's 1A primitive) + the `model=None` degrade path used by offline fakes.
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
