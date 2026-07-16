# Feature Specification: Requirement-Driven Model Selection (consolidation)

**Feature Branch**: `026-model-selection-consolidation`
**Created**: 2026-07-16
**Status**: Draft (revision 3 — rev-2 + contract closure: CallBudget, independence baseline, full-snapshot digest, cold-start, golden-chain preservation, local-verification correction)
**Input**: Prerequisite for the **spec 025 self-improvement lane** (issue [#1242](https://github.com/ContextLab/llmXive/issues/1242); its spec currently lives on branch `025-self-improvement-lane` until it lands). Maintainer decision 2026-07-16: consolidation ships as its own spec + PR, landing first. Consolidate every model-selection site in the platform into one requirement-driven mechanism, keeping a clean boundary between **choosing** a model chain and **executing** it.

## Overview

Model selection is currently scattered across ~25 files: per-agent `default_model` in `agents/registry.yaml` (54 agents), the router's `MODEL_FALLBACKS` + `DEFAULT_MODEL`, the execution tier-ladder (`state/execution_status.py`), the free-model catalog filter (`backends/dartmouth.py`), and ~20 direct model-id pins. This feature replaces that duplication (Constitution I) with **one mechanism** whose defining property is a strict separation of concerns:

```
snap     = runtime_snapshot(...)              # 1. acquisition — composite over ALL backends
                                              #    (inventory + health) + credit balance + paid opt-in;
                                              #    networked, fallible
decision = select(requirement, snap)          # 2. selection — pure, deterministic, testable
response = execute(decision.chain, messages,  # 3. execution — retries, breakers, credit RE-check,
                   options=..., backend_factory=...)  #    fallback
```

The selector never touches the network and reads no environment; it is a **pure function** of `(requirement, runtime_snapshot, selection_policy_version)`. The executor never re-ranks. Call sites express **intent** (a `ModelRequirement`), not a model string. Selection is driven by a **versioned capability policy ∩ the live runtime snapshot**. The migration is **behavior-preserving** (`qwen.qwen3.5-122b` remains the default; the same free-first peer order is retained), and the end state deletes `DEFAULT_MODEL`/`MODEL_FALLBACKS` behind a static enforcement test.

Governed by the constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)): Single Source of Truth (I), Verified Accuracy (II), Real-World Testing (III), Cost Effectiveness / Free-First (IV), Fail Fast (V).

## Scope & Dependencies

**In scope**: the three-layer mechanism (composite runtime snapshot, pure selector + capability policy, execution adapter); the `ModelRef`/`ModelRequirement`/`ModelChain`/`RuntimeSnapshot`/`ExecutionOptions` contracts; multi-level required/preferred independence; requirement-sensitive snapshot-failure semantics; migration of ALL selection sites to requirement profiles; the static enforcement test; deletion of the legacy `DEFAULT_MODEL`/`MODEL_FALLBACKS`.

**Reuse / preserve (Constitution I)**: the executor MUST keep the existing runtime protections in `backends/router.py` — transient/permanent error classification, per-model circuit breakers, retry limits + deadlines, peer fallback, backend fallback — and the paid-credit guard (`backends/credits.py`). `ModelChain` replaces the hard-coded `MODEL_FALLBACKS` *chain*, not these safeguards. The composite snapshot MUST include EVERY configured backend's inventory (e.g. Dartmouth hosted models **and** the local transformers fallback `Qwen/Qwen2.5-3B-Instruct`) so backend fallback needs no second, hidden selection mechanism.

**Downstream**: spec 025's LLM calls (proposer/reviewer/implementer + convergence-panel independence) consume this mechanism; 025's provisional dependency contract is superseded by the richer contract here (025 will be aligned to it once 026 is approved).

## User Scenarios & Testing *(mandatory)*

Stories map to the delivery order (see "Delivery Slices").

### User Story 1 - Composite runtime snapshot & canonical model identity (Priority: P1)

`runtime_snapshot(...)` assembles an immutable, digested snapshot of **every configured backend's** model inventory + health, plus per-model pricing and the current **credit balance** and **paid opt-in** state, recording each component's **age and source**. This is the only networked / environment-reading, fallible layer.

**Why this priority**: Everything else consumes the snapshot; folding catalog + credit + opt-in into one immutable input is exactly what lets `select()` stay pure while still honoring paid limits and backend fallback.

**Independent Test**: Real call — assemble the snapshot; assert each entry resolves to a canonical `ModelRef(backend, serving_endpoint, model_id, model_family, vendor)`, spanning Dartmouth-hosted models AND the local fallback; pricing present (unknown flagged, never free); credit balance + opt-in observed with timestamps; `catalog_digest`, `observed_at`, and per-component `source` (`live` | `last_known_good`).

**Acceptance Scenarios**:
1. **Given** reachable backends, **When** `runtime_snapshot()` runs, **Then** `ModelRef`s distinguish `vendor` (e.g. `openai`) from `serving_endpoint`/`backend` (e.g. Dartmouth) — `openai.gpt-oss-120b` is an OpenAI-family model *served through Dartmouth* — and the local `Qwen/Qwen2.5-3B-Instruct` fallback appears as a distinct low-tier `ModelRef`.
2. **Given** a catalog entry with no pricing, **Then** its cost is `unknown` (NOT free).
3. **Given** a catalog **fetch failure**, **Then** the snapshot marks that component `source=last_known_good` with its true age — distinct from a **successful** fetch that confirms a model's absence (`unavailable`).
4. **Given** the snapshot, **Then** it carries the observed `credit_balance` and `paid_opt_in` with their `observed_at`, so `select()` needs no environment access.
5. **Given** a cold start (no live fetch AND no last-known-good for a component), **When** `runtime_snapshot()` runs, **Then** that component is `source=unavailable` (not `last_known_good`), a downstream paid/fresh-required `select()` fails closed (`ModelUnavailable`), and a low-risk `select()` proceeds on whatever free models are present.

---

### User Story 2 - Pure deterministic selector + capability policy (Priority: P1)

`select(requirement, runtime_snapshot)` is pure: given the same `(requirement, runtime_snapshot, selection_policy_version)` it returns a **byte-identical** ordered `ModelChain`. Eligibility is the **versioned capability policy ∩ the snapshot**; ordering follows fixed tie-breaks; the decision carries per-candidate pricing + an approved per-call credit ceiling into execution.

**Independent Test**: With a fixed fake snapshot, assert repeated `select()` calls return byte-equivalent chains; a model absent from the (successfully-fetched) snapshot is excluded; a capability the policy does not attribute is excluded; unknown price never qualifies as free; `select()` performs no network I/O and reads no environment.

**Acceptance Scenarios**:
1. **Given** identical `(requirement, snapshot, policy_version)`, **When** `select()` runs twice, **Then** the `ModelChain` is byte-identical.
2. **Given** a `deep` requirement with `allow_paid=false`, **Then** the chain is free models led by the highest quality tier (`qwen.qwen3.5-122b`), ordered by tie-breaks: (1) required capabilities satisfied; (2) required independence satisfied; (3) free before paid; (4) preferred quality tier; (5) health/circuit state (if snapshot-backed); (6) estimated cost; (7) stable canonical model id.
3. **Given** a model present but NOT attributed the required capability by the versioned policy, **Then** it is excluded (the catalog proves presence/price, not competence).
4. **Given** `allow_paid=true` with the observed `credit_balance`/`paid_opt_in` in the snapshot, **When** `select()` runs, **Then** it admits a paid candidate ONLY if opt-in is on AND the candidate's worst-case per-call cost — `call_budget.max_input_tokens × input_rate + call_budget.max_output_tokens × output_rate` — fits within both `max_credits` and the observed remaining budget (no environment read).

---

### User Story 3 - Execution adapter consuming a ModelChain (Priority: P1)

`execute(chain, messages, *, options: ExecutionOptions, backend_factory=...)` walks the `ModelChain` under the existing router safeguards, applying `ExecutionOptions` uniformly to every candidate and enforcing paid permission a **second** time immediately before each call. It classifies each per-candidate outcome into exactly one of: **skip-candidate** (ineligible at call time → advance), **retry/advance** (transient / model-unavailable), or **abort-chain** (request-level permanent refusal).

**Independent Test**: With a fake backend factory, assert a transient failure advances the chain; a request-level permanent refusal aborts; a paid candidate whose credit is exhausted by call time is **skipped** (not an abort); `ExecutionOptions.max_tokens`/`temperature`/`deadline` are applied to each candidate.

**Acceptance Scenarios**:
1. **Given** a primary hitting a transient error, **Then** `execute()` advances to the next `ModelRef` (peer, then backend fallback) under the existing breaker/retry/deadline rules.
2. **Given** a **paid-guard denial** at call time (candidate-ineligible), **Then** that candidate is **skipped** and the chain advances — it is NOT a chain abort.
3. **Given** a **request-level permanent refusal** (a hard refusal that would recur on every candidate), **Then** the chain aborts and it is NOT misclassified as transient.
4. **Given** `ExecutionOptions(max_tokens=…, temperature=0.0, deadline=…)`, **Then** those controls apply consistently to every candidate in the chain.

---

### User Story 4 - Required vs. preferred independence (Priority: P2)

`ModelRequirement` expresses *relative* independence via an **`independence_against` baseline** (the prior reviewers' models/families/vendors/endpoints — multi-reviewer capable) plus a **`required_independence`** set (fails closed if unmet) vs **`preferred_independence`** set (may degrade toward the baseline, with a recorded `explanation`). `exclude_*` remain for unconditional prohibitions. Spec 025's convergence panel sets `independence_against` = the prior reviewers, **family diversity required**, **endpoint diversity preferred**.

**Independent Test**: Given `independence_against.families={A,B}`, assert `select()` with `required_independence={"family"}` returns a non-{A,B}-family model or, if none, raises `ModelUnavailable`; assert a `preferred_independence={"serving_endpoint"}` that cannot be met degrades toward the baseline and is recorded in `explanation`.

**Acceptance Scenarios**:
1. **Given** `independence_against.families={A}` and `required_independence={"family"}`, **Then** no family-A model appears in the chain.
2. **Given** `required_independence={"family"}` with no eligible different-family model, **Then** `select()` raises `ModelUnavailable` (025 then does not promote).
3. **Given** `preferred_independence={"serving_endpoint"}` that cannot be met, **Then** selection proceeds, may reuse a baseline endpoint, and records the unmet preference in `ModelChain.explanation`.
4. **Given** `exclude_models={X}` (unconditional), **Then** model X never appears regardless of the baseline.

---

### User Story 5 - Registry / default migration (Priority: P2)

Each `agents/registry.yaml` agent expresses a **requirement profile** rather than a raw `default_model`; registry resolution goes through `select()`. Behavior is preserved against a **fixed migration snapshot** (legacy defaults present); non-LLM sentinels (`deterministic-no-llm`) are exempt from catalog selection.

**Independent Test**: For every LLM agent, assert the resolved primary equals its pre-migration `default_model` under a **fixed migration snapshot**, AND that the full resolved chain byte-matches the legacy `MODEL_FALLBACKS` chain for each legacy primary (**golden-chain assertions**, not merely free→paid ordering); a separate test asserts correct handling under the live snapshot (absence excludes); assert `deterministic-no-llm` agents bypass selection entirely.

**Acceptance Scenarios**:
1. **Given** the fixed migration snapshot, **When** an LLM agent resolves, **Then** its primary matches the pre-migration default (behavior preservation).
2. **Given** the live snapshot where a former default is **absent**, **Then** the selector excludes it and falls to the next eligible candidate (does not resurrect an absent model).
3. **Given** a `deterministic-no-llm` agent, **Then** it is exempt from catalog selection.
4. **Given** `test_config_consistency`, **Then** it validates capability profiles, not a hardcoded model allowlist.

---

### User Story 6 - Execution-tier migration (Priority: P2)

The execution tier-ladder (`FREE_MODEL_TIERS` / `LLMXIVE_EXECUTION_PAID_TIERS`) becomes a **sequence of requirement profiles / escalating constraints** (e.g. free `deep_code` → `allow_paid=true, max_credits=…`), not another list of model ids.

**Independent Test**: Assert tier escalation produces requirements whose `select()` output matches the previous ladder's free→paid ordering under a fixed snapshot + credit state.

**Acceptance Scenarios**:
1. **Given** an escalating run, **When** it bumps a tier, **Then** it bumps a requirement constraint (e.g. `allow_paid`), and `select()` yields the same free-first ordering the ladder previously produced.

---

### User Story 7 - Direct-pin migration + static enforcement (Priority: P2)

The ~20 direct model pins are replaced by requirement profiles. A **static enforcement test** rejects any production model-id literal outside the canonical policy/catalog layer (fixtures + explicit test data allowed), after which `DEFAULT_MODEL` and `MODEL_FALLBACKS` are deleted.

**Independent Test**: Run the static scan over `src/llmxive/**` (excluding the canonical layer + tests/fixtures); assert zero unsanctioned production pins; assert `DEFAULT_MODEL`/`MODEL_FALLBACKS` no longer exist.

**Acceptance Scenarios**:
1. **Given** the migrated tree, **Then** the static scan finds no production model-id literal outside the canonical layer.
2. **Given** migration complete, **Then** `DEFAULT_MODEL` and `MODEL_FALLBACKS` are removed and every call site uses a `ModelRequirement`.

---

### Edge Cases

- **Outage vs confirmed absence**: a failed fetch (`last_known_good`) is distinct from a successful fetch that omits a model (`unavailable`); MUST NOT be conflated.
- **Unknown price**: never free — paid selection fails closed on stale/unknown pricing.
- **Stale snapshot for a high-stakes call**: a spec-025 judgment review requires a fresh-enough snapshot (`max_catalog_age_s` covering catalog AND credit/opt-in components); ordinary low-risk calls may use a bounded last-known-good snapshot.
- **Backend fallback**: the local fallback model is a first-class `ModelRef` in the composite snapshot — no hidden second selection path.
- **Paid race**: allowed at selection, denied at call → **skip candidate**, advance chain (not abort).
- **Independence unmet**: required → `ModelUnavailable` (fail closed); preferred → degrade with recorded explanation.
- **Non-LLM agents**: `deterministic-no-llm` bypasses selection.
- **Test injection**: `select(req, snapshot=fake)` and `execute(chain, options=…, backend_factory=fake)` are the supported seams — replacing the accidental `model=None` degradation.

## Requirements *(mandatory)*

### Separation of concerns
- **FR-001**: The mechanism MUST expose three distinct functions: `runtime_snapshot(...)` (networked/environment-reading, fallible acquisition — composite over all backends + credit balance + paid opt-in), `select(requirement, snapshot) -> ModelChain` (pure, deterministic decision — no network, no env), and `execute(chain, messages, *, options, backend_factory) ` (safe execution). `select()` MUST be a pure function of `(requirement, runtime_snapshot, selection_policy_version)`; `execute()` MUST NOT re-rank.

### Data contracts
- **FR-002**: `ModelRef(backend, serving_endpoint, model_id, model_family, vendor)` — vendor and operational endpoint are separate dimensions. The composite snapshot MUST include every configured backend's models (Dartmouth hosted + local fallback).
- **FR-003**: `ModelRequirement(capability: Literal["cheap","standard","deep","vision"], required_features: frozenset[str], min_context_tokens: int|None, call_budget: CallBudget, independence_against: IndependenceBaseline, required_independence: frozenset[dim], preferred_independence: frozenset[dim], exclude_models: frozenset[str], exclude_families: frozenset[str], exclude_vendors: frozenset[str], exclude_endpoints: frozenset[str], allow_paid: bool, max_credits: int|None, max_catalog_age_s: int, max_candidates: int)`, where `dim ∈ {"model","family","vendor","serving_endpoint"}`. `call_budget = CallBudget(max_input_tokens, max_output_tokens)` gives `select()` everything it needs to bound cost WITHOUT receiving `ExecutionOptions`. `max_credits` (1 credit = $0.001) bounds the **estimated maximum cost of a single call** = `max_input_tokens × input_rate + max_output_tokens × output_rate` (per-model **input and output rates applied separately**); it is NOT chain or daily cost (the daily budget stays the credit guard's job). `exclude_*` are **unconditional prohibitions** (never select these); *relative* independence is expressed separately via `independence_against` (FR-009).
- **FR-004**: `ModelChain(candidates: tuple[Candidate,...], resolved_at, snapshot_digest, snapshot_provenance, selection_policy_version, explanation: tuple[str,...])`, where `snapshot_digest` is a digest of the **complete canonical RuntimeSnapshot** (not just the catalog) and `snapshot_provenance` records each component's (catalog / health / credit / opt-in) age + source that affected the decision; each `Candidate` carries its `ModelRef`, per-candidate **input/output pricing**, and the **approved per-call credit ceiling**. `ModelUnavailable` is raised when no candidate satisfies the requirement.
- **FR-005**: `RuntimeSnapshot(models, pricing [per-model `input_rate` + `output_rate`], health, credit_balance, paid_opt_in, observed_at, sources)`, `CallBudget(max_input_tokens, max_output_tokens)`, `IndependenceBaseline(models, families, vendors, endpoints)` (the prior reviewers to differ from), and `ExecutionOptions(max_tokens, temperature, deadline_s, …)` are immutable typed contracts. `ExecutionOptions` applies uniformly to every candidate; `execute()` MUST enforce `ExecutionOptions.max_tokens ≤ call_budget.max_output_tokens` (the ceiling selection priced against).

### Capability policy & eligibility
- **FR-006**: Eligibility MUST be the intersection of a **versioned capability policy** (a reviewed canonical artifact mapping models → attributed capabilities/features/quality tier) and the live snapshot. The catalog establishes presence/identifier/pricing/(possibly) context limits; it MUST NOT infer competence. Unknown cost MUST NEVER be treated as free.

### Snapshot-failure semantics (requirement-sensitive)
- **FR-007**: Ordinary low-risk calls MAY use a bounded last-known-good snapshot; **paid** selection MUST fail closed on stale/unknown pricing OR stale credit/opt-in observation; spec-025 judgment reviews MUST require a fresh-enough snapshot (`max_catalog_age_s`, applied to catalog AND credit/opt-in components). Absence from a **successfully-fetched** catalog means **unavailable**; a fetch **failure** is distinct. Every decision records component age + source. **Cold start**: a component with neither a live fetch NOR a last-known-good value MUST be marked `source=unavailable` (NOT `last_known_good`); acquisition returns a possibly-partial snapshot and `select()` applies requirement-specific rules — a paid or fresh-required call fails closed (`ModelUnavailable`); a low-risk call MAY proceed on whatever free models are present; if none are present, `ModelUnavailable`.

### Deterministic ordering
- **FR-008**: Given the same `(requirement, snapshot, selection_policy_version)`, `select()` MUST return a byte-identical ordered chain using the tie-breaks: (1) required capabilities satisfied; (2) required independence satisfied; (3) free before paid; (4) preferred quality tier; (5) health/circuit state if snapshot-backed; (6) estimated cost; (7) stable canonical model id. NO model-generated or benchmark-recomputed ranking inside `select()`.

### Independence
- **FR-009**: *Relative* independence is expressed by an **`independence_against` baseline** (the prior reviewers' models/families/vendors/endpoints to differ from) plus a **`required_independence`** set (dimensions where differing from the baseline is mandatory → fail closed `ModelUnavailable` if unmet) and a **`preferred_independence`** set (dimensions where differing is preferred → may degrade *toward* the baseline, recording the unmet preference in `explanation`). This baseline is what makes "preferred" implementable: the selector knows which prior endpoint/family to prefer differing from. `exclude_*` remain ONLY for unconditional prohibitions, independent of the baseline. For spec-025's panel: `independence_against` = the prior reviewers, `required_independence={"family"}`, `preferred_independence={"serving_endpoint"}`.

### Execution safeguards
- **FR-010**: `execute()` MUST preserve the existing router protections (transient/permanent classification, per-model breakers, retry limits + deadlines, peer fallback, backend fallback, paid-credit guard); `ModelChain` replaces the hard-coded `MODEL_FALLBACKS` chain only. Each per-candidate outcome MUST resolve to exactly one of: **skip-candidate** (ineligible at call time, incl. a paid-guard denial → advance), **retry/advance** (transient / model-unavailable), or **abort-chain** (request-level permanent refusal).
- **FR-011**: Paid permission MUST be checked **twice**: at selection time (against the snapshot's observed credit/opt-in, to avoid choosing an unusable model) AND immediately before the call (a live re-check, to prevent a budget/opt-in race).

### Migration (requirements, not renamed pins)
- **FR-012**: Call sites MUST express intent as a `ModelRequirement` via named **requirement profiles** (at least: `cheap_structured`, `standard_generation`, `deep_review`, `deep_code`, `vision`, `independent_review`).
- **FR-013**: Registry agents, the router (`MODEL_FALLBACKS`/`DEFAULT_MODEL`), the execution tier-ladder, the catalog filter, and every direct pin MUST resolve through this mechanism; behavior MUST be preserved (`qwen.qwen3.5-122b` remains the default). The tier-ladder becomes a sequence of requirement profiles / escalating constraints. `deterministic-no-llm` / non-LLM agents are exempt from selection.
- **FR-014**: A **static enforcement test** MUST reject any production model-id literal outside the canonical policy/catalog layer (fixtures + explicit test data allowed). After migration, `DEFAULT_MODEL` and `MODEL_FALLBACKS` MUST be deleted.

### Test seams
- **FR-015**: The mechanism MUST provide supported injection seams — `select(req, snapshot=fake_snapshot)` and `execute(chain, options=…, backend_factory=fake_factory)` — replacing the accidental `model=None` signature degradation the current fakes rely on.

### Key Entities
- **ModelRef**: canonical model identity (backend, serving_endpoint, model_id, model_family, vendor).
- **RuntimeSnapshot**: composite over all backends (models, per-model `input_rate`/`output_rate` pricing, health) + `credit_balance` + `paid_opt_in` + `observed_at` + per-component `source`.
- **CallBudget**: `max_input_tokens`, `max_output_tokens` — the selection input that lets `select()` bound cost without `ExecutionOptions`.
- **IndependenceBaseline**: the prior reviewers to differ from (`models`, `families`, `vendors`, `endpoints`), used with `required_independence`/`preferred_independence`.
- **ModelRequirement**: the call's intent (capability, features, context, `call_budget`, `independence_against` + required/preferred independence, `exclude_*` unconditional prohibitions, paid allowance + `max_credits`, snapshot-freshness, candidate cap).
- **ModelChain / Candidate**: the ordered decision + provenance; `snapshot_digest` binds the full canonical `RuntimeSnapshot` + `snapshot_provenance`; each `Candidate` carries `ModelRef` + input/output pricing + approved per-call credit ceiling.
- **ExecutionOptions**: `max_tokens`, `temperature`, `deadline_s`, … applied uniformly across the chain.
- **CapabilityPolicy**: versioned, reviewed canonical mapping model → attributed capabilities/features/quality tier.
- **RequirementProfile**: a named `ModelRequirement` preset expressing call-site intent.

## Success Criteria *(mandatory)*

- **SC-001**: Same snapshot + requirement + policy_version ⇒ byte-equivalent decision; `select()` does no network I/O and reads no environment (pure-function test).
- **SC-002**: Confirmed catalog absence excludes a model; a catalog outage is distinguished from absence (source recorded).
- **SC-003**: Unknown price never qualifies as free; paid selection fails closed on stale pricing/credit/opt-in.
- **SC-004**: Paid permission is respected at BOTH selection (vs snapshot) and execution (live re-check); a budget/opt-in race skips the candidate rather than overspending.
- **SC-005**: `exclude_*` apply across model/family/vendor/endpoint; required independence unmet ⇒ `ModelUnavailable`; preferred independence unmet ⇒ degraded + recorded.
- **SC-006**: A transient failure advances the chain; a paid-guard denial skips the candidate; a request-level permanent refusal aborts and is not misclassified as transient.
- **SC-007**: Behavior preservation holds against a **fixed migration snapshot** — **golden-chain assertions** reproduce each legacy `MODEL_FALLBACKS` chain byte-for-byte (e.g. `qwen.qwen3.5-122b` → `google.gemma-3-27b-it` → `openai.gpt-oss-120b` → guarded paid — note **`gemma-3-27b-it`, the production peer, NOT `gemma-4`**); a separate live-snapshot test handles absence correctly; `deterministic-no-llm` agents are exempt.
- **SC-008**: Real snapshot assembly + real model calls verify the production integration (Constitution III) across the free tiers (`qwen.qwen3.5-122b`, `openai.gpt-oss-120b`, `google.gemma-4-31B-it`), the vision tier (`qwen.qwen3-vl:32b`), and the local fallback.
- **SC-009**: The static scan finds no unsanctioned production model pins after migration; `DEFAULT_MODEL`/`MODEL_FALLBACKS` are deleted.
- **SC-010**: Backend fallback resolves through the composite snapshot with no separate hidden selection mechanism.

## Delivery Slices

1. **Composite runtime snapshot + canonical model identity** (`ModelRef`, `RuntimeSnapshot`, digest/age/source, credit+opt-in observation). (US1)
2. **Pure deterministic selector + capability policy metadata** (`select`, tie-breaks, `CapabilityPolicy`). (US2)
3. **Execution adapter consuming `ModelChain`** (`ExecutionOptions`; three outcomes; twice-checked paid; router safeguards). (US3)
4. **Independence contract** (required/preferred; `exclude_vendors`; convergence-panel integration). (US4)
5. **Registry / default migration** (profiles; fixed-snapshot behavior preservation; non-LLM exemption). (US5)
6. **Execution-tier migration** (ladder → requirement profiles / escalating constraints). (US6)
7. **Remaining direct-pin migration**. (US7)
8. **Static enforcement test, then delete `DEFAULT_MODEL` + `MODEL_FALLBACKS`**. (US7)

## Assumptions

- This spec is the prerequisite for spec 025; 025 consumes `runtime_snapshot`/`select`/`execute` and the richer contracts here (superseding 025's provisional contract).
- Migration is behavior-preserving: `qwen.qwen3.5-122b` remains the default; the same free-first peer order is retained; no quality-bar change.
- The Dartmouth free + vision models were **real-call verified 2026-07-16** (`qwen.qwen3.5-122b`, `openai.gpt-oss-120b`, `google.gemma-4-31B-it` at cost 0; `qwen.qwen3-vl:32b` present) — availability is timestamped evidence, re-checked at runtime. **Correction (Constitution II):** the local `Qwen/Qwen2.5-3B-Instruct` fallback was NOT real-call verified (it needs optional `transformers` + a checkpoint download); that verification is an **SC-008 task in slice 1**, not a completed claim.
- **Behavior preservation uses the production legacy chain** (`google.gemma-3-27b-it` peer, per `backends/router.py`). Adopting `google.gemma-4-31B-it` would be an **explicit, separately-reviewed capability-policy change**, never a silent swap. *(Flagged for the maintainer: keep gemma-3 for v1, or adopt gemma-4 as a deliberate correction?)*
- `LLMXIVE_PAID_OPT_IN` is OFF by default; the credit guard (`backends/credits.py`) remains the paid gate; `claude-haiku-4-5` remains the sanctioned guarded paid fallback.
- The capability policy is a reviewed canonical artifact; changes to it are normal human PRs, not autonomous.
