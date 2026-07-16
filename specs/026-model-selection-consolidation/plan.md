# Implementation Plan: Requirement-Driven Model Selection (026)

**Branch**: `026-model-selection-consolidation` · **Spec**: [spec.md](./spec.md) · **Status**: revised (plan rev 3, after 2nd critical review)

## Summary

Consolidate all platform model selection into one mechanism with a strict boundary: `runtime_snapshot()` (networked acquisition) → `select(requirement, snapshot)` (pure decision) → `execute(chain, options, backend_factory)` (safe execution + cross-runner credit reservation). Behavior-preserving except the maintainer-approved gemma-3→gemma-4 correction. Ends by deleting `DEFAULT_MODEL`/`MODEL_FALLBACKS` behind a static enforcement test.

**Plan-rev-2 change (critical-review response):** distributed coordination (the reservation ledger) and legacy-router extraction are **system-level changes, not isolated modules**. Added two **prerequisite** slices (router one-candidate primitive; ledger transport + lifecycle), finished LKG persistence in slice 1, added a **checked migration manifest** before migration, and resolved three contract details (health, `resolved_at`, token estimator). See "Review resolutions."

## Technical Context

- **Language**: Python ≥ 3.11 (`src/llmxive/`). **New package**: `src/llmxive/model_selection/`.
- **Modules**: `types.py` (contracts) · `snapshot.py` (`runtime_snapshot`) + `lkg.py` (last-known-good store) · `policy.py` (`CapabilityPolicy` + version) · `select.py` (pure) · `execute.py` (adapter) · `reservations.py` (ledger) · `ledger_transport.py` (git-CAS + sweeper) · `tokens.py` (shared conservative estimator) · `profiles.py` · `enforcement.py` + `inventory.py`.
- **Router extraction (new)**: a one-candidate execution primitive + typed outcomes in `backends/router.py` (see slice 1A) — the seam `execute.py` builds on.
- **Reuse (Constitution I)**: `dartmouth._fetch_cloud_models`/`_model_token_costs`/`_cloud_models_url`; `local.LocalBackend.list_models`; `credits.fetch_credit_balance`/`paid_opt_in_enabled`/`budget_fraction` (+ extend `paid_call_allowed` to accept `estimated_cost_credits`); `router` safeguards (transient/permanent, per-model breakers, retries/deadlines); `tools/summarize._usable_budget`/char-÷4 estimator (basis for `tokens.py`).
- **Testing**: `tests/unit` (pure selector determinism, reservation CAS/state machine + attribution, LKG transitions, enforcement scan — offline); `tests/real_call` (`LLMXIVE_REAL_TESTS=1`): the SC-008 matrix explicitly enumerates a real call through `execute` for **each** of `qwen.qwen3.5-122b`, `openai.gpt-oss-120b`, `google.gemma-4-31B-it`, and the **vision** `qwen.qwen3-vl:32b` — not "a real free call." A **dedicated local-backend lane** (rev-3, P1 #4): a `[local]` optional extra installs transformers+torch and a CI job runs the local-fallback real call with **`importorskip` FORBIDDEN** in that lane (absence = failure, not skip). Plus a **remote integration test using two real git clones** for the ledger CAS (concurrent reservers + sweeper + partial-spend attribution).

## Constitution Check

I (SSoT): one mechanism replaces 5 sites + the full contract surface (manifest-checked); extends the credit guard, not duplicates it. II: real catalog + real call. III: real-call suite + two-clone ledger integration. IV: free-first preserved; paid only under opt-in + reservation ≤ headroom. V: cold-start / stale / independence-unmet / budget-breach / auth-failure all fail closed. ✅

## Review resolutions (from the plan-rev-1 critique)

- **Health (P1 #4 + rev-3):** a freshly-assembled snapshot CANNOT observe per-`DartmouthBackend`-instance breaker state → the v1 selector **does not rank on health** (the tie-break health rung is inactive). But `RuntimeSnapshot.health` **stays** as an **advisory** field (the approved spec includes it; *dropping* it would need a spec revision, *keeping it advisory* does not). `execute()` consults live breaker state as it walks the chain; a shared observable health registry (future) would make the snapshot value authoritative + re-activate the rung.
- **Snapshot provenance ages (P1 #1, rev-3):** introduce `SnapshotProvenance(source, observed_at, age_s)` and use it in `RuntimeSnapshot.sources`, the snapshot digest, and `ModelChain.snapshot_provenance` (replacing the bare `dict[str, SnapshotSource]`) — FR-004/FR-007 require BOTH source AND age in every decision. Slice-1 amendment.
- **`resolved_at` (P2 #6):** `ModelChain.resolved_at = snapshot.observed_at` (derived, injected) — NEVER a clock call inside `select()`, preserving purity + byte-identity (SC-001). Add `resolved_at` back to `ModelChain` (omitted in slice 1) in slice 1's amendment.
- **Token estimator placement (P2 #7 + P1 #3, rev-3):** `select(requirement, snapshot)` has NO messages, so it CANNOT estimate actual input — it prices only the declared `CallBudget`. Design **(a)** (strongest shared-bound): `tokens.py`'s ONE conservative estimator (based on `tools/summarize` char-÷4, deliberately over-estimating, with a defined chat-message serialization + fixed system/tool overhead) is used by the **CALLER to build/validate `CallBudget` from the messages BEFORE `select()`** (so `max_input_tokens ≥ estimated input`), and again by **`execute()` to re-check the actual messages against `CallBudget`** (fail-fast). `select()` itself only reads `CallBudget` and stays pure. Owned by slice 1A; a `call_budget_for(messages, max_output_tokens)` helper does the pre-select construction.

## Slices (revised order)

### Phase 0 — foundation (mechanism must exist + be safe before any migration)

**Slice 1 — contracts + snapshot + LKG.** *(contracts + `runtime_snapshot` DONE; remaining below.)*
- **LKG store** `lkg.py` (fixes P1 #3): atomic write of the last successful snapshot to `state/model_selection/lkg_snapshot.json`; per-component timestamps; digest + `schema_version` validation; corruption → treat as absent; `runtime_snapshot` uses it for the `last_known_good` source. Tests: live→LKG→unavailable transitions; corrupt-file tolerance.
- **Amendments:** introduce `SnapshotProvenance(source, observed_at, age_s)` and use it in `RuntimeSnapshot.sources`, the digest, and `ModelChain.snapshot_provenance` (replacing bare `SnapshotSource`); add `ModelChain.resolved_at` (=`observed_at`); keep `RuntimeSnapshot.health` as an **advisory** field (populated, but NOT ranked by v1 `select`).
- Files: `snapshot.py` (edit), `lkg.py`, `types.py` (edit). Tests: offline LKG + snapshot digest.

**Slice 1A — router one-candidate primitive + typed outcomes + token estimator (NEW prerequisite, fixes P1 #2 + P2 #7).**
- Extract a **one-candidate execution primitive** in `backends/router.py`: run exactly ONE model with the existing safeguards (retries, per-model breaker, deadline) but **NO fallback chain** — the seam `execute.py` walks candidates over. Keep `chat_with_model_fallback`/`chat_with_fallback` intact until migration.
- **Split `PermanentBackendError`** so a **paid-guard denial → skip-candidate** is a distinct type from a **hard refusal → abort-chain**; map every failure to `{skip, retry-advance, abort}`.
- `tokens.py` shared conservative estimator (per "Review resolutions").
- Tests: one-candidate primitive applies safeguards but never falls back; paid-guard-denial vs hard-refusal typing; estimator over-estimates a known message.

**Slice 1B — reservation ledger transport + lifecycle (NEW prerequisite, fixes P0 #1).**
- `ledger_transport.py`: **bootstrap + protection** of `refs/llmxive/credit-ledger`; GitHub Actions **fetch/push config** (which token, which permissions) + auth/permission-failure behavior (fail closed: no paid call if the ledger is unreachable); **strict per-record CAS** transport (fetch→rebuild→verify→append-only→fast-forward→recompute; NOT `commit-and-push.sh`).
- `reservations.py` lifecycle: `open→settling→reconciled` state machine; a **background heartbeat owner** that renews the lease **during the blocking provider call** (thread/async, torn down on return); a **reconciler/sweeper** entry point (a CLI subcommand + a maintenance-workflow step) that settles abandoned reservations, honors the settlement timeout, and performs the **daily-epoch reset** (`budget_epoch`/`settlement_baseline`).
- **Reconciliation attribution (rev-3, P1 #2):** an observed provider-`spend` delta MUST NOT accidentally reconcile multiple overlapping reservations. Rule: order `settling` reservations deterministically (by `created_at`, then idempotency key); reconcile only the **prefix** of that ordered batch whose **cumulative reserved amount is fully covered** by `(observed_spend − settlement_baseline)`; every reservation not fully covered stays `settling` (counting against headroom) until more spend is observed or the daily reset. Never partially-reconcile a single reservation.
- Tests: **two real git clones** — concurrent reservers (only one fast-forwards; loser recomputes); crash-mid-call → sweeper conservatively settles (no leak, no premature reclaim); **two overlapping calls with settlement lag + a PARTIAL spend increase → only the covered prefix reconciles, the rest keep counting** (attribution rule above); daily-reset discards prior-epoch reservations; auth failure fails closed.

### Phase 1 — mechanism

**Slice 2 — pure `select()` + `CapabilityPolicy` + `profiles.py` (fixes P0-adjacent policy shape).** Eligibility = **versioned `CapabilityPolicy` ∩ snapshot**; the policy is a reviewed canonical artifact (`policy.py`) — a versioned table `model → {capabilities, features, quality_tier}` + `selection_policy_version` + a schema test; unknown-to-policy models are ineligible. Deterministic tie-breaks (health rung removed): required capabilities → required independence → free-before-paid → preferred quality tier → **preferred independence** → estimated cost → stable model id. Byte-identical output; no net/env; `resolved_at=snapshot.observed_at`. `ModelUnavailable` on empty/failed. Requirement profiles: `cheap_structured/standard_generation/deep_review/deep_code/vision/independent_review`.

**Slice 3 — `execute()` adapter.** Walks the `ModelChain` over the slice-1A one-candidate primitive; `ExecutionOptions` uniform; three outcomes; `CallBudget` fail-fast via `tokens.py`; reserves via slice-1B; twice-checked paid (`credits.paid_call_allowed(..., estimated_cost_credits=...)`); heartbeat runs during each call.

**Slice 4 — independence eval** in `select`: `independence_against` baseline + required (fail closed) / preferred (degrade + `explanation`); `exclude_*` unconditional.

### Phase 2 — migration (manifest-driven, chokepoints → compatibility consumers)

**Slice M0 — enforcement manifest (NEW, fixes P1 #5).** `inventory.py` generates a **checked manifest** of the ENTIRE contract surface — every `default_model` / `default_backend` / `fallback_backends` / model-id pin — across: `agents/registry.yaml`, **`types.py` (Pydantic `AgentSpec`)**, agent base classes, `cli.py`, Spec Kit commands, run-logging, `web_data.py`, `paper_reprocess/*`, `librarian/*`, and **test doubles**. Committed as `specs/026-.../migration_manifest.md` (or JSON); the slice-8 enforcement test consumes it. Replaces the loose "~20 modules."

**Slice 5 — routing chokepoints.** Migrate the few real routing sites (registry resolution, router `DEFAULT_MODEL`/`MODEL_FALLBACKS` consumers) to `select()`. Golden model-ID projections (paid-off/paid-on; gemma-4). `deterministic-no-llm` exempt. *(The execution-tier ladder is OWNED SOLELY by slice 6 — not here.)*

**Slice 6 — execution-tier migration.** `execution_status.py`/`graph.py` ladder → requirement profiles / escalating constraints; same free→paid ordering.

**Slice 7 — compatibility consumers + schema migration.** Migrate `types.py` (`AgentSpec` fields `default_model`/`default_backend`/`fallback_backends` → capability profile, with a schema migration for persisted execution state that carries model_tier), CLI/web/run-log/paper_reprocess/librarian, and test doubles — each behavior-preserving against the fixed migration snapshot.

**Slice 8 — static enforcement + deletion.** `enforcement.py` scans against the manifest (no unsanctioned production pins outside the canonical layer; fixtures/tests allowed); **gated on the full suite being green**, then delete `DEFAULT_MODEL` + `MODEL_FALLBACKS` and the residual private tables.

## Migration strategy (safety)

Phase 0 is additive (new package + a non-breaking router seam) → the mechanism, the router primitive, and the ledger lifecycle all exist + are tested (incl. two-clone integration) before any call-site change. Phase 1 completes the pure/execute boundary. Phase 2 is manifest-driven and incremental: chokepoints first, then compatibility consumers + schema migration, each behavior-preserving (golden chains). Slice 8 is the only irreversible step, gated on green. `qwen.qwen3.5-122b` stays default throughout; gemma-4 replaces gemma-3 (approved correction).

## Complexity Tracking

Two genuinely system-level pieces, each isolated to its slice + justified:
- **Ledger transport + lifecycle (slice 1B):** the maintainer chose a strong (not best-effort) cross-runner fractional-cap guarantee; needs real git-CAS transport + a background heartbeat + a sweeper + two-clone tests. Engages only on paid calls (rare; opt-in off by default).
- **Router one-candidate extraction (slice 1A):** required because `execute()` must apply safeguards to ONE candidate without the legacy fallback chain (else double-fallback or duplicated logic). Done as a non-breaking seam before any deletion.
