# Feature Specification: Requirement-Driven Model Selection (consolidation)

**Feature Branch**: `026-model-selection-consolidation`
**Created**: 2026-07-16
**Status**: Draft
**Input**: Prerequisite for spec [025 self-improvement lane](../025-self-improvement-lane/spec.md) (maintainer decision 2026-07-16: consolidation ships as its own spec + PR, landing first). Consolidate every model-selection site in the platform into one requirement-driven mechanism, keeping a clean boundary between **choosing** a model chain and **executing** it.

## Overview

Model selection is currently scattered across ~25 files: per-agent `default_model` in `agents/registry.yaml` (54 agents), the router's `MODEL_FALLBACKS` + `DEFAULT_MODEL`, the execution tier-ladder (`state/execution_status.py`), the free-model catalog filter (`backends/dartmouth.py`), and ~20 direct model-id pins. This feature replaces that duplication (Constitution I) with **one mechanism** whose defining property is a strict separation of concerns:

```
snapshot = catalog_snapshot(...)          # 1. acquisition — networked, fallible
decision = select(requirement, snapshot)  # 2. selection — pure, deterministic, testable
response = execute(decision.chain, ...)    # 3. execution — retries, breakers, credits, fallback
```

The selector never touches the network; the executor never re-ranks. Call sites express **intent** (a `ModelRequirement`), not a model string. Selection is driven by a **versioned capability policy ∩ a live availability/pricing snapshot**. The migration is **behavior-preserving** (`qwen.qwen3.5-122b` remains the default; the same free-first peer order is retained), and the end state deletes `DEFAULT_MODEL`/`MODEL_FALLBACKS` behind a static enforcement test.

Governed by the constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)): Single Source of Truth (I), Verified Accuracy (II), Real-World Testing (III), Cost Effectiveness / Free-First (IV), Fail Fast (V).

## Scope & Dependencies

**In scope**: the three-layer mechanism (catalog snapshot, pure selector + capability policy, execution adapter); the `ModelRef`/`ModelRequirement`/`ModelChain` contracts; multi-level independence; requirement-sensitive catalog-failure semantics; migration of ALL selection sites to requirement profiles; the static enforcement test; deletion of the legacy `DEFAULT_MODEL`/`MODEL_FALLBACKS`.

**Reuse / preserve (Constitution I)**: the executor MUST keep the existing runtime protections in `backends/router.py` — transient/permanent error classification, per-model circuit breakers, retry limits + deadlines, peer fallback, backend fallback — and the paid-credit guard (`backends/credits.py`). `ModelChain` replaces the hard-coded `MODEL_FALLBACKS` *chain*, not these safeguards.

**Downstream**: spec 025's LLM calls (proposer/reviewer/implementer + convergence-panel independence) consume this mechanism; 025's provisional dependency contract is superseded by the richer contract here.

## User Scenarios & Testing *(mandatory)*

Stories map to the delivery order (see "Delivery Slices").

### User Story 1 - Catalog snapshot & canonical model identity (Priority: P1)

`catalog_snapshot(...)` fetches the live Dartmouth catalog and returns a typed, digested snapshot of `ModelRef`s + pricing + (where available) context limits, recording the snapshot's **age and source**. This is the only networked, fallible layer.

**Why this priority**: Everything else consumes a snapshot; isolating acquisition makes selection pure and testable.

**Independent Test**: Real call — fetch the live catalog; assert each entry resolves to a canonical `ModelRef(backend, serving_endpoint, model_id, model_family, vendor)`, pricing is present (unknown cost is flagged, never treated as free), and the snapshot carries `catalog_digest`, `resolved_at`, and `source` (`live` | `last_known_good`).

**Acceptance Scenarios**:
1. **Given** a reachable catalog, **When** `catalog_snapshot()` runs, **Then** it returns a snapshot whose `ModelRef`s distinguish `vendor` (e.g. `openai`) from `serving_endpoint`/`backend` (e.g. Dartmouth) — because `openai.gpt-oss-120b` is an OpenAI-family model *served through Dartmouth*.
2. **Given** a catalog entry with no pricing, **When** it is snapshotted, **Then** its cost is `unknown` (NOT free).
3. **Given** a catalog fetch failure, **When** `catalog_snapshot()` runs, **Then** it returns a snapshot marked `source=last_known_good` with its true age — distinct from a successful fetch that confirms a model's absence.

---

### User Story 2 - Pure deterministic selector + capability policy (Priority: P1)

`select(requirement, snapshot)` is a pure function: given the same `requirement`, `snapshot`, and `selection_policy_version`, it returns a **byte-identical** ordered `ModelChain`. Eligibility is the **versioned capability policy ∩ the live snapshot**; ordering follows fixed tie-breaks.

**Why this priority**: A deterministic, auditable decision is exactly what spec 025 (and the whole platform) needs; it is trivially unit-testable with a fixed snapshot.

**Independent Test**: With a fixed fake snapshot, assert repeated `select()` calls return byte-equivalent chains; a model absent from the (successfully-fetched) snapshot is excluded; a capability the policy does not attribute to a model excludes it; unknown price never qualifies as free.

**Acceptance Scenarios**:
1. **Given** identical `(requirement, snapshot, policy_version)`, **When** `select()` runs twice, **Then** the `ModelChain` is byte-identical.
2. **Given** a `deep` requirement with `allow_paid=false`, **When** `select()` runs, **Then** the chain is free models led by the highest quality tier (`qwen.qwen3.5-122b`), ordered by the tie-breaks: (1) required capabilities satisfied; (2) free before paid; (3) preferred quality tier; (4) health/circuit state (if snapshot-backed); (5) estimated cost; (6) stable canonical model id.
3. **Given** a model present in the catalog but NOT attributed the required capability by the versioned policy, **When** `select()` runs, **Then** it is excluded (the catalog proves presence/price, not competence).
4. **Given** `select()`, **When** it ranks, **Then** it performs NO model-generated or benchmark-recomputed ranking (the policy is a reviewed canonical artifact).

---

### User Story 3 - Execution adapter consuming a ModelChain (Priority: P1)

`execute(chain, messages, *, backend_factory=...)` walks the `ModelChain` under the existing router safeguards, enforcing paid permission a **second** time immediately before each call. It preserves — does not replace — transient/permanent classification, per-model breakers, retry/deadline limits, peer + backend fallback, and the credit guard.

**Why this priority**: Selection must not weaken the hard-won runtime resilience; the boundary is "choose the chain" vs "execute it safely."

**Independent Test**: With a fake backend factory, assert a transient failure walks to the next `ModelRef` in the chain; a permanent refusal aborts (not misclassified as transient); a paid `ModelRef` is skipped if the credit guard denies it at call time even though selection allowed it.

**Acceptance Scenarios**:
1. **Given** a chain whose primary hits a transient error, **When** `execute()` runs, **Then** it walks to the next `ModelRef` (peer, then backend fallback) under the existing breaker/retry rules.
2. **Given** a permanent refusal (e.g. paid-guard denial, hard refusal) on the primary, **When** `execute()` runs, **Then** it is NOT misclassified as transient.
3. **Given** a paid `ModelRef` allowed at selection time, **When** the credit budget is exhausted by call time, **Then** the immediate-pre-call check skips it (twice-checked paid permission).

---

### User Story 4 - Convergence-panel independence (Priority: P2)

`ModelRequirement` expresses independence via `exclude_models` / `exclude_families` / `exclude_endpoints` (so it can exclude *several* prior reviewers, not just one). Spec 025's convergence panel **requires family diversity when available** and records endpoint diversity separately; if the required diversity cannot be met, selection fails closed (`ModelUnavailable`).

**Why this priority**: Genuine review diversity needs a different model *family*, and outage isolation a different *serving endpoint* — a single `independent_of: str` cannot express either across multiple reviewers.

**Independent Test**: Given prior reviewers on families {A, B}, assert `select()` with `exclude_families={A,B}` returns a different family or, if none is available, raises `ModelUnavailable` (fail closed); assert endpoint diversity is recorded in the decision `explanation`.

**Acceptance Scenarios**:
1. **Given** `exclude_families={A}`, **When** `select()` runs, **Then** no family-A model appears in the chain.
2. **Given** exclusions that leave no eligible model, **When** `select()` runs, **Then** it raises `ModelUnavailable` (025 then does not promote).
3. **Given** a returned chain, **When** inspected, **Then** the `ModelChain.explanation` records which independence dimensions (model/family/vendor/endpoint) were satisfied.

---

### User Story 5 - Registry / default migration (Priority: P2)

Each `agents/registry.yaml` agent expresses a **requirement profile** (e.g. `deep_review`, `standard_generation`) rather than a raw `default_model`; registry resolution goes through `select()`. Behavior is preserved (the default resolves to `qwen.qwen3.5-122b`).

**Independent Test**: For every registry agent, assert the resolved primary model equals its pre-migration `default_model` under the current catalog (behavior preservation), and that resolution flows through `select()`.

**Acceptance Scenarios**:
1. **Given** a migrated registry, **When** an agent resolves its model, **Then** the resolved primary matches the pre-migration default (no behavior change).
2. **Given** `test_config_consistency`, **When** it runs, **Then** it validates capability profiles (not a hardcoded model allowlist).

---

### User Story 6 - Execution-tier migration (Priority: P2)

The execution tier-ladder (`FREE_MODEL_TIERS` / `LLMXIVE_EXECUTION_PAID_TIERS`) becomes a **sequence of requirement profiles / escalating constraints** (e.g. free `deep_code` → `allow_paid=true, max_credits=…`), not another list of model ids.

**Independent Test**: Assert tier escalation produces requirements whose `select()` output matches the previous ladder's free→paid ordering under the current catalog + credit guard.

**Acceptance Scenarios**:
1. **Given** an escalating execution run, **When** it bumps a tier, **Then** it bumps a requirement constraint (e.g. `allow_paid`), and `select()` yields the same free-first ordering the ladder previously produced.

---

### User Story 7 - Direct-pin migration + static enforcement (Priority: P2)

The ~20 direct model pins across `librarian/`, `claims/`, `fill/`, `agents/`, `convergence/`, `tools/`, etc. are replaced by requirement profiles. A **static enforcement test** then rejects any production model-id literal outside the canonical policy/catalog layer (fixtures + explicit test data allowed), after which `DEFAULT_MODEL` and `MODEL_FALLBACKS` are deleted.

**Independent Test**: Run the static scan over `src/llmxive/**` (excluding the canonical layer + tests/fixtures); assert zero unsanctioned production pins; assert `DEFAULT_MODEL`/`MODEL_FALLBACKS` no longer exist.

**Acceptance Scenarios**:
1. **Given** the migrated tree, **When** the static scan runs, **Then** it finds no production model-id literal outside the canonical layer.
2. **Given** the migration is complete, **When** the codebase is inspected, **Then** `DEFAULT_MODEL` and `MODEL_FALLBACKS` are removed and every call site uses a `ModelRequirement`.

---

### Edge Cases

- **Catalog outage vs confirmed absence**: a failed fetch (`last_known_good`) is distinct from a successful fetch that omits a model (`unavailable`); the two MUST NOT be conflated.
- **Unknown price**: never qualifies as free — paid selection fails closed on stale/unknown pricing.
- **Stale snapshot for a high-stakes call**: a spec-025 judgment review requires a fresh-enough snapshot (`max_catalog_age_s`); an ordinary low-risk call may use a bounded last-known-good snapshot.
- **Independence unmet**: `ModelUnavailable` (fail closed), never a silent same-family fallback.
- **Paid race**: allowed at selection, denied at call → skipped by the immediate pre-call check.
- **Test injection**: `select(req, snapshot=fake_snapshot)` and `execute(chain, ..., backend_factory=fake_factory)` are the supported seams — replacing the accidental `model=None` signature degradation the current fakes rely on.
- **Model served by multiple endpoints**: vendor/family vs serving_endpoint are separate dimensions; endpoint diversity is trackable independently of family diversity.

## Requirements *(mandatory)*

### Separation of concerns
- **FR-001**: The mechanism MUST expose three distinct functions: `catalog_snapshot(...)` (networked, fallible acquisition), `select(requirement, snapshot) -> ModelChain` (pure, deterministic decision), and `execute(chain, messages, *, backend_factory=...)` (safe execution). `select()` MUST NOT perform network I/O; `execute()` MUST NOT re-rank.

### Data contracts
- **FR-002**: `ModelRef(backend, serving_endpoint, model_id, model_family, vendor)` — vendor and operational endpoint are separate dimensions (a vendor's model may be served through a different backend/endpoint).
- **FR-003**: `ModelRequirement(capability: Literal["cheap","standard","deep","vision"], required_features: frozenset[str], min_context_tokens: int|None, exclude_models: frozenset[str], exclude_families: frozenset[str], exclude_endpoints: frozenset[str], allow_paid: bool, max_credits: int|None, max_catalog_age_s: int, max_candidates: int)`. Independence is expressed by the `exclude_*` sets (multi-reviewer capable). `max_credits` is in **credits** (1 credit = $0.001) with explicit enforcement semantics.
- **FR-004**: `ModelChain(candidates: tuple[ModelRef,...], resolved_at: datetime, catalog_digest: str, selection_policy_version: int, explanation: tuple[str,...])`. `ModelUnavailable` is raised when no candidate satisfies the requirement.

### Capability policy & eligibility
- **FR-005**: Eligibility MUST be the intersection of a **versioned capability policy** (a reviewed canonical artifact mapping models → attributed capabilities/features/quality tier) and the **live availability/pricing snapshot**. The catalog establishes presence/identifier/pricing/(possibly) context limits; it MUST NOT be used to infer competence at code review, strict JSON, deep reasoning, or vision.
- **FR-006**: Unknown cost MUST NEVER be treated as free.

### Catalog-failure semantics (requirement-sensitive)
- **FR-007**: Ordinary low-risk calls MAY use a bounded last-known-good snapshot; **paid** selection MUST fail closed on stale/unknown pricing; spec-025 judgment reviews MUST require a fresh-enough snapshot (`max_catalog_age_s`). Absence from a **successfully-fetched** catalog means **unavailable**; a fetch **failure** is distinct from confirmed absence. Every decision MUST record snapshot age + source.

### Deterministic ordering
- **FR-008**: Given the same `(requirement, snapshot, selection_policy_version)`, `select()` MUST return a byte-identical ordered chain, using the tie-breaks: (1) required capabilities satisfied; (2) free before paid; (3) preferred quality tier; (4) current health/circuit state if snapshot-backed; (5) estimated cost; (6) stable canonical model id. NO model-generated or benchmark-recomputed ranking inside `select()`.

### Independence
- **FR-009**: The mechanism MUST support independence at four levels: `different_model`, `different_family`, `different_vendor`, `different_serving_endpoint`. For spec-025's convergence panel it MUST require **family diversity when available** and record **endpoint diversity** separately; if the required diversity level cannot be met it MUST fail closed (`ModelUnavailable`).

### Execution safeguards
- **FR-010**: `execute()` MUST preserve the existing router protections (transient/permanent classification, per-model circuit breakers, retry limits + deadlines, peer fallback, backend fallback, paid-credit guard); `ModelChain` replaces the hard-coded `MODEL_FALLBACKS` chain only.
- **FR-011**: Paid permission MUST be checked **twice**: at selection time (to avoid choosing an unusable model) AND immediately before the call (to prevent a budget/opt-in race).

### Migration (requirements, not renamed pins)
- **FR-012**: Call sites MUST express intent as a `ModelRequirement` via named **requirement profiles** (at least: `cheap_structured`, `standard_generation`, `deep_review`, `deep_code`, `vision`, `independent_review`); the goal is NOT to move model strings into a new dictionary.
- **FR-013**: Registry agents (`default_model`), the router (`MODEL_FALLBACKS`/`DEFAULT_MODEL`), the execution tier-ladder, the catalog filter, and every direct pin MUST resolve through this mechanism; behavior MUST be preserved (`qwen.qwen3.5-122b` remains the default). The execution tier-ladder becomes a sequence of requirement profiles / escalating constraints.
- **FR-014**: A **static enforcement test** MUST reject any production model-id literal outside the canonical policy/catalog layer (fixtures + explicit test data allowed). After migration, `DEFAULT_MODEL` and `MODEL_FALLBACKS` MUST be deleted.

### Test seams
- **FR-015**: The mechanism MUST provide supported injection seams — `select(req, snapshot=fake_snapshot)` and `execute(chain, ..., backend_factory=fake_factory)` — replacing the accidental `model=None` signature degradation the current fakes rely on.

### Key Entities
- **ModelRef**: canonical model identity (backend, serving_endpoint, model_id, model_family, vendor).
- **ModelRequirement**: the call's intent (capability, features, context, exclusions, paid allowance + credit cap, snapshot-freshness, candidate cap).
- **ModelChain**: the ordered decision + provenance (candidates, resolved_at, catalog_digest, selection_policy_version, explanation).
- **CatalogSnapshot**: live availability + pricing + digest + age + source (`live`|`last_known_good`).
- **CapabilityPolicy**: versioned, reviewed canonical mapping model → attributed capabilities/features/quality tier.
- **RequirementProfile**: a named `ModelRequirement` preset expressing call-site intent.

## Success Criteria *(mandatory)*

- **SC-001**: Same snapshot + requirement + policy_version ⇒ byte-equivalent decision.
- **SC-002**: Confirmed catalog absence excludes a model; a catalog outage is distinguished from absence (source recorded).
- **SC-003**: Unknown price never qualifies as free.
- **SC-004**: Paid selection AND execution both respect opt-in + credit budget (twice-checked).
- **SC-005**: Independence exclusions apply across model, family, and endpoint; no eligible independent model ⇒ `ModelUnavailable`.
- **SC-006**: A transient failure walks the returned chain; a permanent refusal is not misclassified as transient.
- **SC-007**: Existing registry callers preserve behavior during migration (resolved primary == prior default under the current catalog).
- **SC-008**: Real catalog fetch + real model calls verify the production integration (Constitution III), across the free tiers (`qwen.qwen3.5-122b`, `openai.gpt-oss-120b`, `google.gemma-4-31B-it`) and the vision tier (`qwen.qwen3-vl:32b`).
- **SC-009**: The static scan finds no unsanctioned production model pins after migration; `DEFAULT_MODEL`/`MODEL_FALLBACKS` are deleted.
- **SC-010**: `select()` performs no network I/O and no model-generated ranking (pure-function test).

## Delivery Slices

1. **Catalog snapshot + canonical model identity** (`ModelRef`, `CatalogSnapshot`, digest/age/source). (US1)
2. **Pure deterministic selector + capability policy metadata** (`select`, tie-breaks, `CapabilityPolicy`). (US2)
3. **Execution adapter consuming `ModelChain`** (preserving router safeguards; twice-checked paid). (US3)
4. **Convergence-panel integration + independence constraints** (multi-level; family diversity; fail closed). (US4)
5. **Registry / default migration** (agents → requirement profiles; behavior preserved). (US5)
6. **Execution-tier migration** (ladder → requirement profiles / escalating constraints). (US6)
7. **Remaining direct-pin migration**. (US7)
8. **Static enforcement test, then delete `DEFAULT_MODEL` + `MODEL_FALLBACKS`**. (US7)

## Assumptions

- This spec is the prerequisite for spec 025; 025 consumes `catalog_snapshot`/`select`/`execute` and the richer contracts here (superseding 025's provisional contract).
- Migration is behavior-preserving: `qwen.qwen3.5-122b` remains the default; the same free-first peer order is retained; no quality-bar change.
- The three free models + vision model are live (real-call verified 2026-07-16: `qwen.qwen3.5-122b`, `openai.gpt-oss-120b`, `google.gemma-4-31B-it` at cost 0; `qwen.qwen3-vl:32b` for vision) — but model availability is timestamped evidence, re-checked at runtime.
- `LLMXIVE_PAID_OPT_IN` is OFF by default; the credit guard (`backends/credits.py`) remains the paid gate; `claude-haiku-4-5` remains the sanctioned guarded paid fallback.
- The capability policy is a reviewed canonical artifact; changes to it are normal human PRs, not autonomous.
