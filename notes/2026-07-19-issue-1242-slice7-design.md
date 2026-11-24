# spec 026 — Slice 7 DESIGN (rev 2): compatibility consumers + `AgentRegistryEntry` schema migration

**Tracking issue** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Branch**
`026-model-selection-consolidation` · **Date** 2026-07-19 (rev 2 after design review) ·
**Predecessor** [Slice 6 handoff](2026-07-18-issue-1242-slice6-handoff.md) · **Kickoff**
[Slices 7–8 kickoff](2026-07-18-issue-1242-slices-7-8-kickoff.md)

## Relationship to issue #1242 (traceability)

Spec 026 does **NOT** implement #1242's acceptance criteria. #1242 ("self-improvement through
lessons learned") asks for two cron-driven self-improvement lanes with isolated branches, canaries
and circuit breakers. Spec 026 is the **model-selection prerequisite** for spec 025's lane, split off
as its own spec + PR by maintainer decision 2026-07-16 (recorded at `spec.md:6`). This slice is
judged against spec 026's FR/SC criteria, tracked at **#1285**. Earlier notes in this series are
named `issue-1242-*` for lineage only; that naming asserts a traceability that does not hold and is
not continued here.

## Work-list (authoritative)

ALL **300** `owning_slice==7` rows in `specs/026-model-selection-consolidation/migration_manifest.json`:

|category|rows|cleared by|
|-|-|-|
|`migration_target`|136|§5 (direct pins) + §1 (the 91 `field_consumer` rows)|
|`registry`|161|§1, in one schema rewrite|
|`schema`|3|§1 (`types.py` `AgentRegistryEntry`)|

The 1 `exempt` row (`agents/registry.yaml:866`, `paper_publisher`'s `deterministic-no-llm`) carries no
`owning_slice` but MUST be rehomed by §1. `test_double` (267) and `canonical_layer` (7) are not
Slice-7 work. **Slice 7 is not done while any `owning_slice==7` row survives the live scan.**

## Maintainer decisions

|#|Decision|Chosen|
|-|-|-|
|D1|`_VISION_MODEL` pin vs the `vision` profile|**Attribute `vision` to `qwen3.5` in the policy** (the pin is right; the policy table was incomplete). Gated on real-call verification of actual image *understanding* — §4.|
|D2|Tier-1 "exclude the registered default" once `default_model` is gone|**`exclude_leader`**, implemented as a **two-pass routing translation** (§3) — NOT a `select()` post-process.|
|D3|Registry schema shape|**Delete `default_model` / `default_backend` / `fallback_backends`, add `profile`.**|
|D4|Run-log attribution on the pre-call failure path|**Nullable `backend`/`model_name` + a SUCCESS validator requiring BOTH.**|
|D5|`paper_reviewer_figure_critic`'s profile|**`deep_review`** (vision intent lives at the real vision call site).|
|D6|The figure-review call bypasses the backend layer and cannot carry multimodal content|**Extend the canonical path to multimodal** (§4.1) so the call genuinely routes through `select()`/`execute()` with all FR-010 safeguards.|
|D7|Is `AgentRegistryEntry.paid_opt_in` real per-agent authorization?|**Retain the field with its ORIGINAL narrowed meaning; do NOT thread it as a routing ceiling** (rev-2's ceiling would have broken SC-007(b) — reversed in rev 3, §1.2).|
|D8|Traceability|**File a spec-026 issue (#1285)** and reference both it and the #1242 derivation.|

## Hard constraints (inherited)

- Behavior-preserving against the **fixed migration snapshot**: `qwen.qwen3.5-122b` stays the leader
  for every LLM agent; `gemma-4` stays.
- No model-id literals outside the canonical policy/catalog layer.
- Regenerate the manifest after every pin move (frozen-drift test).
- Full non-slow suite green; commit each step with `PRE_COMMIT_ALLOW_NO_CONFIG=1` + the
  `Co-Authored-By` trailer; **do NOT push**.
- Do not touch `agents/prompts/**` (would fire the promptfoo eval gate).

---

## §1 — The registry-entry schema

`AgentRegistryEntry` (`src/llmxive/types.py:689`) drops `default_model`, `default_backend`,
`fallback_backends`; gains `profile`. `paid_opt_in` **stays** (D7, §1.2).

### §1.1 Profile validation without an import cycle (review finding 6)

A **runtime** `from llmxive.model_selection.profiles import PROFILES` inside `types.py` would cycle:
importing any `model_selection` submodule executes `model_selection/__init__.py:21`, which imports
`execute` → `backends.router` → back into a partially-initialized `llmxive.types`. `TYPE_CHECKING`
does not help a runtime validator.

**Resolution:** declare the names as a `Literal` in the schema layer, with **no import at all**:

```python
# src/llmxive/types.py — no model_selection import
ProfileName = Literal[
    "cheap_structured", "standard_generation", "deep_review",
    "deep_code", "vision", "independent_review", "deterministic-no-llm",
]

class AgentRegistryEntry(_Strict):
    profile: ProfileName
    ...
```

plus a unit test asserting `set(get_args(ProfileName)) - {"deterministic-no-llm"} == set(PROFILES)`,
so the two cannot drift. Pydantic gives a load-time failure on an unknown profile (Constitution V).

### §1.2 `paid_opt_in`: retained, narrowed, NOT a routing ceiling (D7 — REVERSED in rev 3)

**Rev 2 proposed** `allow_paid_eff = snap.credit.paid_opt_in and entry.paid_opt_in`, to make the
per-agent flag "real authorization." **That was wrong and is reversed.** Since all 54 agents set
`paid_opt_in: false`, the conjunction is always false, so the guarded paid tail would vanish from
**every ordinary registry call** — breaking SC-007(b) ("paid opt-in ON with headroom → that sequence
plus the guarded paid fallback", `spec.md:228`). That is a new behavior change well outside the
sanctioned deltas, not the activation of dormant authorization.

The legacy behavior confirms the narrower reading: `MODEL_FALLBACKS` carried the `claude-haiku` peer
for **all** agents, and `test_config_consistency:85` gates it as "only PEER fallbacks may be a guarded
paid model" — never per-agent. The guarded tail was never conditioned on `entry.paid_opt_in`.

**Contract (unchanged from as-built):**

- The paid gate stays **process-level**: `LLMXIVE_PAID_OPT_IN` + the credit guard + the reservation
  ledger. `route.py:199` (`allow_paid_eff = snap.credit.paid_opt_in`) is **not** modified.
- `AgentRegistryEntry.paid_opt_in` is **retained** with its original documented meaning, narrowed
  explicitly in its docstring: it permits an agent to configure a **paid-preferring default or
  profile**; it does **NOT** prohibit the platform's globally-enabled guarded fallback.
- No Slice-7 profile requires paid, so the field has no routing consumer this slice. That is
  intentional: it is a declaration surface governed by the `types.py:701-705` constitutional comment,
  not a per-call gate.
- The Slice-6 escalation ladder is therefore untouched — tier 2 needs no override semantics, because
  no per-agent ceiling exists to override.

### §1.3 Consumers

The 91 `field_consumer` rows collapse mechanically: every
`default_backend=…, fallback_backends=…, model=…` triple becomes `profile=entry.profile`. Consumers:
`agents/base.py`, `implementer.py`, `librarian.py`, `paper_reviewer.py`, `personality.py`,
`submission_intake.py`, `task_verifier.py`, `living_document.py`, `grounding_guard.py`, `cli.py`,
`pipeline/graph.py`, `paper_reprocess/{branch_code,branch_nocode,code_adapter}.py`, and the
`speckit/*_cmd.py` + `slash_command.py` family. `SlashCommandContext`'s `default_backend` /
`fallback_backends` / `default_model` fields are replaced by a single `profile`.

**Why deleting the backend fields is safe:** `route_chat` has ignored them since Slice 5 — backend
fallback is first-class in the selected chain. All 54 agents carry identical values (`dartmouth`,
`[local]`), so no per-agent information is lost.

## §2 — Per-agent profile assignment

|profile|n|agents|
|-|-|-|
|`deep_review`|26|`research_reviewer`, `paper_reviewer`, the 12 `paper_reviewer_*` specialists (incl. `figure_critic`, per D5), the 7 `research_reviewer_*` specialists, `research_question_validator`, `reference_validator`, `proofreader`, `repository_hygiene`, `idea_selector`|
|`standard_generation`|16|`brainstorm`, `flesh_out`, `project_initializer`, `librarian`, `specifier`, `clarifier`, `planner`, `tasker`, `paper_initializer`, `paper_specifier`, `paper_clarifier`, `paper_planner`, `paper_tasker`, `paper_writing`, `task_atomizer`, `personality`|
|`deep_code`|7|`implementer`, `paper_implementer`, `llmxive_implementer`, `code_adapter`, `paper_figure_generation`, `latex_fix`, `paper_statistics`|
|`cheap_structured`|4|`latex_build`, `status_reporter`, `task_joiner`, `submission_intake`|
|`deterministic-no-llm`|1|`paper_publisher`|

Total 54. No registry agent gets `independent_review` (it needs a caller-supplied
`independence_against` baseline that registry dispatch does not provide); it stays the programmatic
preset for spec 025's convergence panel.

**Why US5 AC1 holds by construction.** All 53 LLM agents pin `qwen.qwen3.5-122b`, and the policy gives
family `qwen3.5` quality-tier 3 with `{cheap, standard, deep}` — above `gemma-4`/`gpt-oss` (tier 2)
and ahead of paid `claude-haiku` by free-before-paid (FR-008). So under the fixed migration snapshot
**every profile still leads with `qwen3.5`**: `cheap`/`standard`/`deep` by capability, `vision` once
§4 lands, and `independent_review` because an empty baseline makes family-independence vacuous while
the offline snapshot is `live` at age 0.0. Mis-assignment is therefore low-risk for the *leader* and
shows up only in the tail — but the AC1 test asserts all 53 leaders, so it stays a real guard.

### §2.1 `max_candidates` — express intent, verified by per-profile projections (review finding 8)

The review objected that raising four profiles from 4 to 8 is "not automatically behavior-preserving."
**The baseline runs the other way.** Every registry agent and every direct-pin caller currently routes
through the *provisional* `standard_generation` — hardcoded at `router.py:320` (`_walker_route`) and
`router.py:435` (`chat_with_fallback`) — which carries `max_candidates=8` (`profiles.py:103`). So
assigning `deep_review` at its default cap of 4 is a **reduction** from as-built behavior for 37
agents; raising to 8 **preserves** it. Slice 5 raised `standard_generation` precisely because 4
truncated the guarded paid tail under the live COMPOSITE snapshot (qwen3.5 → gemma-4 → gpt-oss →
local qwen2.5 fills the cap before the paid tail) — see `profiles.py:95-103`.

**The review's remedy is adopted regardless:** caps express intent, verified rather than homogenized.
Each profile gets a **composite-snapshot chain projection test** (not the 3-model offline snapshot)
asserting its exact intended chain. Any cap that ends up *below* the as-built 8 is recorded as an
**intentional delta** with its rationale — notably `cheap_structured`, where a narrower/cheaper
fallback surface is arguably correct — never as a silent side effect of a profile default.

## §3 — Tier-1 without a registered default (D2, review finding 4)

The rev-1 design was internally inconsistent: it put `exclude_leader` on `RequirementOverrides` while
saying `select()` applies it, but `select()` receives a `ModelRequirement` and `route_chat` consumes
overrides via `replace(base, …)`. Post-processing a selected chain would also mean the chain is no
longer the direct output of `select(requirement, snapshot)`, complicating the US6 independent test.

**Resolution — a two-pass translation in routing, keeping `select()` untouched and pure:**

```python
# route_chat, after composing overrides onto the base requirement
if overrides is not None and overrides.exclude_leader:
    first = select(requirement, snap)                      # pure pass 1
    leader = first.candidates[0].model_ref.model_id
    requirement = replace(
        requirement, exclude_models=requirement.exclude_models | {leader}
    )
chain = select(requirement, snap)                          # pure pass 2 — THE decision
```

Both passes are pure and I/O-free, so the cost is negligible and the returned chain **is** the direct
output of `select(requirement, snapshot)`. `FR-003`/the data model need no amendment.
`TierConstraint.exclude_registered_default` → `exclude_leader`; `to_overrides()` / `tier_overrides()`
drop their `default_model` parameter, so `graph.py:767` and `:773` stop needing a model id.

**Behavior preservation is exact** under the fixed snapshot: excluding-the-leader and
excluding-`qwen3.5` are the same operation while `qwen3.5` *is* the leader, so Slice 6's tier-1 golden
(`gemma-4` leads) is unchanged.

**Tests (review-requested):** interaction with required independence (an excluded leader cascading
into an independence failure), pre-existing `exclude_models`, a live-absent former default, quality
ties, `max_candidates` truncation, and pass 1 raising `ModelUnavailable` — which **propagates
immediately; pass 2 is never invoked** (rev-2 said "pass 2 must too", which was incoherent).

**No persisted-state migration.** `state/execution_status/<project>.json` stores `model_tier` as an
integer *index*; Slice 6 already converted the rungs to `RequirementOverrides`. Only the dispatch-time
argument leaked a model id. The kickoff's "persisted-state schema migration" therefore resolves to
**verify the tier state machine and counters are untouched** (a regression test), not migrate them.

## §3.5 — `deterministic-no-llm` needs BOTH layers (review finding 3)

`route.py:168` detects the sentinel only via `caller_model == DETERMINISTIC_NO_LLM`. Once
`caller_model` is gone, `profile="deterministic-no-llm"` would reach `build_requirement()` and die as
an unknown-profile `KeyError` — possibly after snapshot/ledger preparation. Required:

1. **Registry dispatch bypasses no-LLM agents entirely** — the agent runner checks
   `entry.profile == DETERMINISTIC_NO_LLM` and never builds messages or enters routing.
2. **Defense in depth:** `route_chat` raises `ValueError` on `profile == DETERMINISTIC_NO_LLM`
   **before** snapshot acquisition (keeping the current early position at `route.py:168`, re-keyed
   from `caller_model` to `profile`).

**US5 AC3 tests BOTH layers**, not just the route guard.

## §4 — Vision: multimodal execution, then the policy correction

### §4.1 The blocker (D6, review finding 2)

`preprint_figures._review_one_figure` does not merely use a custom request — it **bypasses the entire
backend layer**: it builds its own HTTP body (`model`, `max_tokens`, `temperature`,
`extra_body.chat_template_kwargs.enable_thinking`), sets its own `Bearer` header, and calls
`urllib.request.urlopen(..., timeout=180)` against `_endpoint()`. No `BaseBackend`, no breaker, no
retry envelope, no classification, no credit guard, no `execute()`. And the structural blocker sits
below the transport: `ChatMessage.content` is typed **`str`** on a frozen dataclass
(`backends/base.py:22-24`), so the `list[dict]` payload carrying the `image_url` data URI cannot be
expressed as a `ChatMessage` at all. `profile="vision"` was **not implementable** as rev 1 wrote it.

**Resolution (D6): extend the canonical path.** Only two backends implement `chat()`
(`local.py:39`, `dartmouth.py:744`) plus the abstract `base.py:171`, so the contract change is
tractable:

- `ChatMessage.content: str | tuple[ContentPart, ...]`, where `ContentPart` is a small frozen union
  (`TextPart(text)` / `ImagePart(mime, data, width, height)`). A plain `str` stays valid — every
  existing caller is unaffected.
- **`ImagePart` validates** `mime` (an allowlist), `width`/`height` against the documented maximum
  (§4.1.2), and a bounded encoded byte size. Without this a caller could submit an arbitrarily large
  payload while being charged a fixed token estimate.
- `DartmouthBackend.chat` serializes parts into the OpenAI content array (the existing
  `enable_thinking=False` handling is already backend-level SSoT, so the figure call stops carrying
  its own copy).
- `LocalBackend.chat` **rejects** multimodal input — see §4.1.1 for the exception CLASS, which is
  load-bearing.
- `execute()` passes content through unchanged; its FR-010 fail-fast budget check must handle parts
  using the SAME estimator selection used (§4.1.2).
- `preprint_figures` then deletes `_VISION_MODEL` and its urllib path and calls
  `route_chat(profile="vision", max_tokens=2000, temperature=0)`.

#### §4.1.1 A permanent rejection would ABORT, not skip (review finding 2)

Rev 2 claimed a permanent typed error from `LocalBackend` would be "skipped." **The disposition
contract does the opposite.** `router.py:205-213` classifies:

```
PaidGuardDenied        -> SKIP            (checked BEFORE its PermanentBackendError base)
BackendUnavailable     -> RETRY_ADVANCE   (breaker open)
TransientBackendError  -> RETRY_ADVANCE
PermanentBackendError  -> ABORT           <-- a naive "unsupported multimodal" error lands here
unknown                -> ABORT           (conservative)
```

So an "unsupported multimodal input" `PermanentBackendError` would **abort the whole chain**,
violating FR-010/SC-006.

**Resolution:** introduce `UnsupportedFeatureError` — a candidate-ineligibility class whose
disposition is **SKIP**, checked before its `PermanentBackendError` base, exactly mirroring the
existing `PaidGuardDenied` split. This is more robust than relying on selection to guarantee a
text-only model never enters a vision chain, because multimodal content may later be used with
profiles other than `vision`. Test: a chain whose first candidate is text-only **advances** to the
vision-capable peer instead of aborting.

#### §4.1.2 Image pricing must be a demonstrable UPPER bound (review finding 3)

Rev 2's "generous fixed constant + a test that pricing exceeds a realistic floor" **proves the wrong
direction.** `worst_case_credits` is an *upper* bound under FR-003/FR-010; a floor test says nothing
about underestimation, which is the dangerous failure. Real image token cost varies with dimensions,
tiling/detail mode, and provider serialization.

**Resolution — bounded inputs + a documented worst case:**

- `ImagePart` enforces documented **maximum dimensions**; images exceeding them are **rejected**
  (fail fast, Constitution V) rather than silently under-priced.
- The per-image token charge is a **documented worst-case constant derived from those maximum
  dimensions and the detail mode** the backend requests — recorded with its derivation, not chosen
  by feel.
- Tests assert the estimator returns **at least the documented maximum** for representative
  *boundary* images (max-dimension, max-byte-size), not merely above an average-looking floor.
- `execute()`'s pre-call input check uses **exactly the same estimator** as selection, so the bound
  it reserves against and the bound it enforces cannot diverge.

#### §4.1.3 Repository-wide `content` audit (review requirement)

Changing `ChatMessage.content` reaches beyond the two `chat()` implementations. Task 3 includes a
repo-wide audit of every `.content` usage: token counting, inspection/audit serialization, test
doubles, message copying/`replace`, and any code doing string operations (`len`, slicing, `+`,
regex) on `.content`. Each site either keeps its `str` fast path or handles parts explicitly.

This is what FR-010/FR-013 actually require, and it is the only option that does not either leave a
sanctioned pin behind or duplicate `execute()`'s safeguards in a second executor (Constitution I).

### §4.2 The policy correction (D1)

`CAPABILITY_POLICY["qwen3.5"]` gains `"vision"` in `capabilities` and `features`;
`SELECTION_POLICY_VERSION` 1 → 2 (a policy change that can alter a decision MUST bump the version —
it is part of `select()`'s pure input, SC-001). The figure call then resolves to
`qwen.qwen3.5-122b` — identical model to today — with `qwen3-vl:32b` as the tier-2 peer behind it.

**Gate (Constitution II) — TWO required real calls, not one (review finding 5).**

1. **`qwen.qwen3.5-122b` image *understanding*** — justifies the new attribution. Asserting payload
   acceptance is insufficient: the test renders a figure with a known, checkable visual property and
   asserts the response reports it (a model that ignored the image cannot). **If this fails, STOP and
   escalate** — the fallback is migrating the call to `qwen3-vl` as a sanctioned delta, which also
   needs `qwen3-vl` added to the conftest offline snapshot.
2. **`qwen.qwen3-vl:32b` through `execute()`** — required **independently** by SC-008, which names
   the vision tier as that model (`spec.md:229`; plan.md:17 enumerates a real call through `execute`
   for it). Rev 2 made it a fallback but required no call to it. This also proves the selected
   fallback can consume the new canonical multimodal representation.

Both require `DARTMOUTH_CHAT_API_KEY` and live in `tests/real_call/` beside the SC-008 matrix.

**Exact test fallout of the version bump** (located, not predicted):

|test|change|
|-|-|
|`tests/unit/test_model_selection_policy.py:20`|`… == SELECTION_POLICY_VERSION == 1` → `== 2`|
|`tests/unit/test_model_selection_select.py:488`|`chain.selection_policy_version == 1` → `== 2`|
|`tests/unit/test_model_selection_select.py:271`|`vision`-profile leader becomes `qwen.qwen3.5-122b`, `qwen3-vl:32b` the peer|

`test_model_selection_policy.py:47-48` (`qwen3-vl` is vision-only, NOT `deep`) and
`test_model_selection_select.py:264` are **unaffected** — adding `vision` to `qwen3.5` does not change
`qwen3-vl`'s attribution.

## §5 — Direct pins (43 rows) + the interface migration

### §5.1 All four wrappers take `profile` (review finding 5)

Rev 1 omitted `chat_with_fallback` — the **primary registry path** — which hardcodes
`profile="standard_generation"` at `router.py:435`. The contract is:

- `_walker_route`, `reasoning_chat`, `chat_with_model_fallback`, **and `chat_with_fallback`** all
  accept `profile: str = "standard_generation"` (the default preserves unmigrated callers).
- Once its callers migrate, `chat_with_fallback` **drops** `default_backend`, `fallback_backends` and
  `model` from its signature (`router.py:387-396`).
- **Object state, not just function signatures:** reviewer/reviser/agent objects that today store a
  `_model` (or equivalent) store a **profile** instead. Changing only the wrapper functions is
  insufficient — the review is right that this is where a half-migration would hide.
- **Secondary call paths** are covered explicitly, not just the manifest-listed literals: reviser
  self-consistency passes, the malformed-response retry loop (`base.py:151-159`), and any helper API
  still exposing an optional `model=` parameter. The zero-manifest-row gate does not catch an
  interface that merely *permits* a pin, so these are enumerated in the plan.

### §5.2 Profile per intent

|intent|profile|sites|
|-|-|-|
|extraction / classification / structured parse|`cheap_structured`|`claims/extract.py`, `claims/resolve.py`, `fill/extract.py`, `fill/service.py`, `librarian/query_extractor.py`, `librarian/math_classifier.py`, `librarian/data_source_discovery.py`, `execution/data_source.py`, `tools/summarize.py:248`|
|review / entailment / triage / judgment|`deep_review`|`grounding/entailment.py`, `agents/grounding_guard.py`, `convergence/triage.py`, `convergence/engine.py:400`, `librarian/relevance_judge.py`, `agents/task_verifier.py`, `agents/living_document.py`|
|revision of code + specs|`deep_code`|the `convergence/revisers/*` family|
|figure review|`vision`|`paper_reprocess/preprint_figures.py` (after §4.1)|
|persona generation|`standard_generation`|`agents/personality.py:68` (`MODEL_NAME`)|

### §5.3 Two reclassifications

- `backends/local.py:37` `list_models` → `canonical_layer`. It is the local backend **declaring its
  own inventory** — a snapshot *input*, not a selection pin; deleting it would blind the composite
  snapshot (SC-010).
- `tools/summarize.py:45` `_MODEL_BUDGETS` → **deleted**, read `policy.max_context_tokens(family)`
  instead (Constitution I). The one §5 change with real behavior surface: assert the resolved budgets
  match the current table for the models it covers.

`backends/dartmouth.py:510` `KNOWN_FREE_MODELS` stays this slice (Slice 8 deletes it); Slice 7 only
removes `test_config_consistency`'s dependency on it.

## §6 — Tests: US5 AC1, AC3, AC4 + run-log attribution

**AC1 (new, binding):** for all 53 LLM agents, under the fixed migration snapshot, assert the
`select()` leader is `qwen.qwen3.5-122b`; assert `paper_publisher` never reaches selection.

**AC3 (§3.5):** both the registry-dispatch bypass and the `route_chat` pre-snapshot guard.

**AC4 — rewrite `tests/unit/test_config_consistency.py`,** dropping the `KNOWN_FREE_MODELS` /
`MODEL_FALLBACKS` imports at lines 25-26:

|current test|becomes|
|-|-|
|`test_registry_models_are_free_unless_paid_opt_in` (:59)|every agent's `profile` is canonical; under a **paid-opt-in-OFF** snapshot every profile's chain is free-only; with opt-in ON **and headroom**, the guarded paid tail appears — **independent of `entry.paid_opt_in`** (§1.2, preserving SC-007(b)). Asserts the *production* routing path, not a differently-constructed requirement.|
|`test_model_fallback_chains_are_free` (:77)|the **policy** admits no paid family except the sanctioned `claude-haiku-4-5`|
|`test_every_llm_registry_model_has_a_fallback_chain` (:95)|every profile resolves to ≥2 candidates (the outage-stranding guard, re-expressed)|
|`test_readme_model_names_match_registry` (:134)|re-pointed at the policy table — the registry no longer names models|

**`README.md`'s "Models & cost" section is updated in the same commit** (the test enforces it).

**Run-log attribution (D4):** `RunLogEntry.backend` → `BackendName | None`, `model_name` →
`str | None`, with a validator requiring **both** non-`None` when `outcome is Outcome.SUCCESS` (a
half-populated successful entry is rejected). `agents/base.py:137-138` stops seeding from the registry
and records only what happened; the success path already overwrites from `response.backend`/`.model`
at `base.py:162-163`. Verified safe: `state/runlog.py:237` filters non-SUCCESS **before** building
paper authorship, and `pipeline/authors.py:207-213` null-guards both fields. `ReviewRecord`
(`types.py:618`) already uses this nullable+validator idiom.

## §8 — Spec amendments (review finding 4) — REQUIRED, not optional

Two Slice-7 semantics currently live only in this design, while `spec.md` says the only general
migration delta is Gemma-3→Gemma-4 and US6's sanctioned text specifically says tier 1 excludes **the
registered default**. Left unrecorded, a future review would correctly flag the implementation as
drift. `spec.md` MUST be amended in the same slice:

|amendment|where|
|-|-|
|Tier 1's semantics change from "exclude the registered default" to **"exclude whatever `select()` ranks first"** — necessarily, since the registered default ceases to exist (§3). Behavior is identical under the fixed snapshot.|US6 "Sanctioned migration delta" paragraph|
|`qwen3.5` gains the **`vision`** capability, widening vision eligibility and incrementing `SELECTION_POLICY_VERSION` to 2 (§4.2). Verified by real call.|Assumptions + a new sanctioned-delta note alongside the Gemma correction|
|SC-007 gains a note that the vision projection's leader is `qwen.qwen3.5-122b` with `qwen3-vl:32b` as peer.|SC-007|

These are amendments to a **binding, approved spec** — they get written as explicit sanctioned
deltas with their rationale, in the same style as the Slice-6 tier-1 delta already recorded there.

## §7 — Task sequencing (each independently green + committed)

|#|task|clears|
|-|-|-|
|1|`exclude_leader` two-pass translation in `route_chat` + `execution_status`/`graph.py` de-parameterization|§3|
|2|`deterministic-no-llm` two-layer bypass + AC3|§3.5|
|3|**Multimodal canonical path**: `ContentPart` + `ImagePart` validation, `UnsupportedFeatureError` SKIP class, both backends, `execute()` passthrough, upper-bound image pricing, repo-wide `.content` audit|§4.1|
|4|**Two real-call vision verifications** (qwen3.5 understanding → policy `vision` + `SELECTION_POLICY_VERSION` 2; qwen3-vl through `execute()` for SC-008). STOP + escalate if #1 fails|§4.2|
|5|`ProfileName` Literal + `AgentRegistryEntry` schema + 54 registry entries + `SlashCommandContext` (`paid_opt_in` retained, docstring narrowed — NOT threaded)|§1, 161+3 rows|
|6|the 91 `field_consumer` sites|§1.3|
|7|all four wrappers take `profile`; object-state + secondary-path interface migration; the 43 direct pins|§5.1-5.2|
|8|`_MODEL_BUDGETS` → policy; `local.py` reclassification in `inventory.py`|§5.3|
|9|`RunLogEntry` nullable + validator + `base.py` attribution|§6|
|10|AC1 test + per-profile composite projections (§2.1) + `test_config_consistency` rewrite + README|§2.1, §6|
|11|**`spec.md` amendments** (tier-1 semantics, qwen3.5 vision, SC-007 vision projection)|§8|
|12|manifest regeneration + full non-slow suite + zero surviving `owning_slice==7` rows|all|

Manifest regenerates after every pin-moving task, not only at task 12.

### Required tests for the multimodal task (review-specified)

Dartmouth serialization of text AND image parts · existing string messages remaining
byte-equivalent · unsupported-feature **skip** behavior (chain advances, does not abort) · mixed
text/image token accounting **at maximum dimensions** · retry/fallback preserving immutable content ·
inspection capture serializing image **metadata** without duplicating raw image bytes into audit logs ·
paid vision candidates reserving against the **image-inclusive** estimate.

## Risks

|risk|mitigation|
|-|-|
|Vision real-call verification fails|Task 4 is gated and STOPS the slice; the `qwen3-vl` fallback is pre-designed.|
|Multimodal contract change breaks a backend, a test double, or a `.content` string consumer|Only 2 `chat()` implementations; `str` content stays valid so existing callers are untouched; §4.1.3's repo-wide `.content` audit is part of task 3, not an afterthought.|
|A text-only backend ABORTS a vision chain instead of skipping|`UnsupportedFeatureError` with SKIP disposition (§4.1.1), mirroring the existing `PaidGuardDenied` split; tested by a chain that must advance past a text-only candidate.|
|Image token pricing under-estimates → an invalid cost bound|Bounded `ImagePart` (max dimensions + byte size, oversize REJECTED) + a worst-case constant derived from those bounds + boundary tests asserting the estimator is **≥** the documented maximum (§4.1.2). The same estimator gates execution.|
|Slice-7 semantics read as drift in a later review|§8 amends `spec.md` (US6 tier-1 wording, the qwen3.5 vision delta, the SC-007 vision projection) as an explicit slice task.|
|A profile mis-assignment goes unnoticed|Leaders are all `qwen3.5` under the fixed snapshot, so AC1 cannot catch a wrong-but-plausible profile. Per-profile composite projections (§2.1) catch capability/tail mistakes; assignment is reviewed per task.|
|Deleting `default_backend` breaks a test double|The schema change is a load-time failure — breakage is loud, not silent.|

## Definition of done (Slice 7)

Zero surviving `owning_slice==7` manifest rows; `AgentRegistryEntry` carries `profile` and no model
ids (`paid_opt_in` retained, un-threaded, docstring narrowed); `exclude_leader` replaces the tier-1
model-id exclusion; the multimodal path lands with a SKIP-class unsupported-feature error and a
demonstrable image-pricing upper bound, and the figure call routes through `execute()`; US5 AC1 +
AC3 + AC4 landed; README consistent with the policy table; **both** vision real calls verified
(qwen3.5 understanding + qwen3-vl through `execute()` for SC-008); `spec.md` amended with the
sanctioned Slice-7 deltas; full non-slow suite green. **Then** Slice 8.
