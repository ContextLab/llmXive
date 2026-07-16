# Implementation Plan: Requirement-Driven Model Selection (026)

**Branch**: `026-model-selection-consolidation` · **Spec**: [spec.md](./spec.md) · **Status**: in progress

## Summary

Consolidate all platform model selection into one mechanism with a strict boundary: `runtime_snapshot()` (networked acquisition) → `select(requirement, snapshot)` (pure decision) → `execute(chain, options, backend_factory)` (safe execution + cross-runner credit reservation). Behavior-preserving except the maintainer-approved gemma-3→gemma-4 correction. Ends by deleting `DEFAULT_MODEL`/`MODEL_FALLBACKS` behind a static enforcement test.

## Technical Context

- **Language**: Python ≥ 3.11 (existing package `src/llmxive/`).
- **New package**: `src/llmxive/model_selection/` — `types.py` (contracts), `snapshot.py` (`runtime_snapshot`), `policy.py` (`CapabilityPolicy` + `selection_policy_version`), `select.py` (pure `select`), `execute.py` (adapter), `reservations.py` (credit reservation ledger), `profiles.py` (requirement profiles), `enforcement.py` (static scan).
- **Reuse (Constitution I)**: `backends/dartmouth.py` (catalog fetch, `model_token_costs`, `free_chat_models`), `backends/router.py` (safeguards — transient/permanent, breakers, retries, peer/backend fallback), `backends/credits.py` (extend `paid_call_allowed` to accept `estimated_cost_credits`), `backends/local.py` (local fallback inventory), `scripts/ci/commit-and-push.sh` NOT for the ledger CAS (dedicated strict CAS instead).
- **Testing**: `tests/unit` (pure selector determinism, reservation CAS/state machine, enforcement scan — offline); `tests/real_call` (`LLMXIVE_REAL_TESTS=1`: real `runtime_snapshot`, real free-model call through `execute`, local fallback). Gemma golden chains as model-ID projections under paid-off/paid-on conditions.

## Constitution Check

- **I (SSoT)**: replaces 5 scattered selection sites + ~20 pins with one mechanism; extends the canonical credit guard rather than duplicating it. ✅
- **II (Verified Accuracy)**: real catalog + real call verification (SC-008); model availability is timestamped, re-checked. ✅
- **III (Real-World Testing)**: real-call suite exercises the production router path + local fallback. ✅
- **IV (Free-First)**: free-first ordering preserved; paid only under opt-in + reservation ≤ headroom. ✅
- **V (Fail Fast)**: cold-start / stale-snapshot / independence-unmet / budget-breach all fail closed. ✅

## Slice → files → tests (delivery order)

| Slice | Files | Key tests |
|-|-|-|
|1 Snapshot + identity|`types.py` (ModelRef, RuntimeSnapshot, CreditGuardSnapshot, CallBudget, ExecutionOptions, IndependenceBaseline, ModelRequirement, ModelChain, Candidate), `snapshot.py`|real `runtime_snapshot` spans Dartmouth + local; vendor≠endpoint; unknown-price≠free; cold-start `source=unavailable`; credit-guard headroom observed|
|2 Pure selector + policy|`policy.py`, `select.py`, `profiles.py`|byte-identical decision (fixed snapshot); capability∩snapshot; tie-break order incl. preferred-independence; no network/env; `ModelUnavailable`|
|3 Execute + reservation|`execute.py`, `reservations.py`, extend `credits.py`|transient walks / paid-guard skip / permanent abort; CallBudget fail-fast; strict-CAS ledger at `refs/llmxive/credit-ledger`; open→settling→reconciled; deadline lease + heartbeat; cross-runner concurrency + leak tests|
|4 Independence|`select.py` (independence eval)|required→ModelUnavailable; preferred→degrade+explanation; exclude_* unconditional|
|5 Registry migration|`agents/registry.yaml` (capability profiles), registry resolution, `checks/prompts.py`/`test_config_consistency`|golden model-ID projections (gemma-4); non-LLM `deterministic-no-llm` exempt; live-absence excludes|
|6 Tier migration|`state/execution_status.py`, `pipeline/graph.py`|ladder→requirement profiles; same free→paid ordering|
|7 Pin migration|~20 modules (librarian/claims/fill/agents/convergence/tools/…)|each call site uses a `ModelRequirement`; behavior preserved|
|8 Static enforcement|`enforcement.py` + a test; delete `DEFAULT_MODEL`/`MODEL_FALLBACKS`|scan finds no unsanctioned production pins; legacy symbols gone|

## Migration strategy (safety)

Slices 1–4 are additive (new package, no call-site change) → the mechanism exists + is tested before any migration. Slices 5–7 migrate call sites incrementally, each behavior-preserving (golden chains) and independently committable. Slice 8 is the irreversible cleanup, gated on the full suite being green. `qwen.qwen3.5-122b` stays the default throughout; gemma-4 replaces gemma-3 (approved correction) — asserted by the golden-chain projections.

## Complexity Tracking

The cross-runner reservation ledger (strict CAS on `refs/llmxive/credit-ledger`) is the most complex piece; justified by the maintainer's choice of a strong (not best-effort) fractional-cap guarantee under concurrent paid calls. It is self-contained in `reservations.py` and only engages on paid calls (rare; opt-in off by default).
