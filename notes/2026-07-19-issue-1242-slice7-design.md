# Issue #1242 / spec 026 — Slice 7 DESIGN (compatibility consumers + `AgentRegistryEntry` schema migration)

**Branch** `026-model-selection-consolidation` · **Date** 2026-07-19 · **Predecessor**
[Slice 6 handoff](2026-07-18-issue-1242-slice6-handoff.md) · **Kickoff**
[Slices 7–8 kickoff](2026-07-18-issue-1242-slices-7-8-kickoff.md)

Slice 7 retires the last model-id pins outside the canonical policy/catalog layer and lands US5's
deferred, still-binding acceptance criteria (AC1, AC4). Slice 8 (enforcement + deletions) follows and
is NOT in scope here.

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

## Maintainer decisions (2026-07-18/19, this session)

|#|Decision|Chosen|
|-|-|-|
|D1|`_VISION_MODEL` pin vs the `vision` profile|**Attribute `vision` to `qwen3.5` in the policy** (the pin is right; the policy table was incomplete). Gated on real-call verification — see §4.|
|D2|Tier-1 "exclude the registered default" once `default_model` is gone|**Add `exclude_leader` to `RequirementOverrides`**; `select()` drops rank-1.|
|D3|Registry schema shape|**Delete all three fields, add `profile`.**|
|D4|Run-log attribution on the pre-call failure path|**Nullable `backend`/`model_name` + a SUCCESS validator.**|
|D5|`paper_reviewer_figure_critic`'s profile|**`deep_review`** (vision intent lives at the real vision call site).|

## Hard constraints (inherited)

- Behavior-preserving against the **fixed migration snapshot**: `qwen.qwen3.5-122b` stays the leader
  for every LLM agent; `gemma-4` stays. The ONE sanctioned delta is D1's policy attribution, which is
  behavior-*preserving* at the call site (still `qwen3.5`) and only widens eligibility.
- No model-id literals outside the canonical policy/catalog layer.
- Regenerate the manifest after every pin move (frozen-drift test).
- Full non-slow suite green; commit each step with `PRE_COMMIT_ALLOW_NO_CONFIG=1` + the
  `Co-Authored-By` trailer; **do NOT push**.
- Import-cycle discipline: `model_selection` types into `backends`/`agents` under `TYPE_CHECKING` +
  `from __future__ import annotations`.
- Do not touch `agents/prompts/**` (would fire the promptfoo eval gate; Slice 7 is schema, so N/A).

---

## §1 — The registry-entry schema

`AgentRegistryEntry` (`src/llmxive/types.py:689`) drops `default_model`, `default_backend`,
`fallback_backends`; gains:

```python
profile: str  # validated against set(PROFILES) | {"deterministic-no-llm"}
```

Validation lives in `types.py` so an unknown profile is a **load-time** failure (Constitution V), and
the registry can only name intents the mechanism implements. `deterministic-no-llm` survives as a
reserved `profile` value, so `paper_publisher`'s exemption and `route.DETERMINISTIC_NO_LLM` keep
working — only the field they read changes.

**Why deleting the backend fields is safe, not bold:** `route_chat` has ignored `default_backend` /
`fallback_backends` since Slice 5 — backend fallback is first-class in the selected chain (the local
candidate carries `backend=="local"`). They have been decorative config for two slices. All 54 agents
carry the identical values (`dartmouth`, `[local]`), so there is no per-agent information to lose.

The 91 `field_consumer` rows then collapse mechanically: every
`default_backend=…, fallback_backends=…, model=…` argument triple becomes `profile=entry.profile`.
Consumers: `agents/base.py`, `implementer.py`, `librarian.py`, `paper_reviewer.py`, `personality.py`,
`submission_intake.py`, `task_verifier.py`, `living_document.py`, `grounding_guard.py`, `cli.py`,
`pipeline/graph.py`, `paper_reprocess/{branch_code,branch_nocode,code_adapter}.py`, and the
`speckit/*_cmd.py` + `slash_command.py` family. `SlashCommandContext.default_backend` /
`fallback_backends` / `default_model` are replaced by a single `profile` field on the same dataclass.

## §2 — Per-agent profile assignment

|profile|n|agents|
|-|-|-|
|`deep_review`|26|`research_reviewer`, `paper_reviewer`, the 12 `paper_reviewer_*` specialists (incl. `figure_critic`, per D5), the 7 `research_reviewer_*` specialists, `research_question_validator`, `reference_validator`, `proofreader`, `repository_hygiene`, `idea_selector`|
|`standard_generation`|16|`brainstorm`, `flesh_out`, `project_initializer`, `librarian`, `specifier`, `clarifier`, `planner`, `tasker`, `paper_initializer`, `paper_specifier`, `paper_clarifier`, `paper_planner`, `paper_tasker`, `paper_writing`, `task_atomizer`, `personality`|
|`deep_code`|7|`implementer`, `paper_implementer`, `llmxive_implementer`, `code_adapter`, `paper_figure_generation`, `latex_fix`, `paper_statistics`|
|`cheap_structured`|4|`latex_build`, `status_reporter`, `task_joiner`, `submission_intake`|
|`deterministic-no-llm`|1|`paper_publisher`|

Total 54. No registry agent gets `independent_review`: that profile requires a caller-supplied
`independence_against` baseline, which registry dispatch does not provide; it stays the programmatic
preset for spec 025's convergence panel.

**Why US5 AC1 holds by construction.** All 53 LLM agents currently pin `qwen.qwen3.5-122b`, and the
policy gives family `qwen3.5` quality-tier 3 with `{cheap, standard, deep}` — strictly above `gemma-4`
and `gpt-oss` (tier 2), and ahead of paid `claude-haiku` by the free-before-paid rung (FR-008). So
under the fixed migration snapshot **every profile still leads with `qwen3.5`**: `cheap`/`standard`/
`deep` by capability, `vision` once §4 lands, and `independent_review` because an empty independence
baseline makes family-independence vacuous while the offline snapshot is `live` at age 0.0 (clearing
its 900 s freshness gate). Mis-assignment is therefore low-risk for the leader and shows up only in
the fallback tail — but the AC1 test asserts all 53 leaders so it stays a real guard if the policy
ever shifts.

### §2.1 — `max_candidates` must be aligned across the text profiles (consequence of §2)

`standard_generation` carries `max_candidates=8`; the other five profiles still default to `4`. Slice
5 raised it for `standard_generation` specifically because 4 **truncated the guarded paid tail** under
the live COMPOSITE snapshot (qwen3.5 → gemma-4 → gpt-oss → local qwen2.5 fills the cap before the paid
`claude-haiku` tail) — see the recorded rationale at `model_selection/profiles.py:95-103`. Moving 37
agents onto `deep_review` / `deep_code` / `cheap_structured` would silently reintroduce that
truncation for them. It is invisible offline because the test snapshot holds only 3 models.

**Decision:** raise `max_candidates` to 8 on `cheap_structured`, `deep_review`, `deep_code`, and
`vision`, with the same rationale comment. `independent_review` keeps a tighter cap (it deliberately
narrows to independent families). This preserves the legacy `MODEL_FALLBACKS` chain shape
(free peers → guarded paid tail) for every migrated agent, which is what behavior-preservation means
under the live snapshot.

## §3 — Tier-1 without a registered default (D2)

`RequirementOverrides` gains `exclude_leader: bool = False`. `select()` applies it **after ordering,
before truncating to `max_candidates`**, dropping the rank-1 candidate. `TierConstraint`'s
`exclude_registered_default` becomes `exclude_leader`, and `to_overrides()` / `tier_overrides()` lose
their `default_model` parameter — so `pipeline/graph.py:767` (`_model_for_run = entry.default_model`,
carrying Slice 6's `# Slice 7 owns per-agent base profiles` marker) and `graph.py:773` stop needing a
model id at all.

**Behavior preservation is exact** under the fixed snapshot: excluding-the-leader and
excluding-`qwen3.5` are the same set operation while `qwen3.5` *is* the leader, so Slice 6's tier-1
golden (`gemma-4` leads) is unchanged.

**No persisted-state migration is required.** `state/execution_status/<project>.json` stores
`model_tier` as an integer *index*, not a model id; Slice 6 already converted the rungs to
`RequirementOverrides`. Only the dispatch-time argument leaked a model id, so this is a signature
change, not a file-format change. In-flight projects keep their tier untouched. The kickoff's
"persisted-state schema migration" concern resolves to: **verify** the tier state machine and its
counters are untouched (a regression test), not migrate them.

## §4 — The vision policy correction (D1) — VERIFICATION-GATED

`CAPABILITY_POLICY["qwen3.5"]` gains `"vision"` in both `capabilities` and `features`;
`SELECTION_POLICY_VERSION` 1 → 2 (a policy change that can alter a decision MUST bump the version —
it is part of `select()`'s pure input, SC-001). `paper_reprocess/preprint_figures.py:34`
`_VISION_MODEL` is deleted; `vision_figure_review` routes with `profile="vision"`, resolving to
`qwen.qwen3.5-122b` — **identical behavior**, now expressed as intent, with `qwen3-vl:32b` as the
tier-2 peer behind it.

**Gate (Constitution II).** This ships ONLY after a real call proves `qwen.qwen3.5-122b` accepts image
input. The comment at `preprint_figures.py:30` asserts it ("qwen3.5-122b is vision-capable … accepts
the whole figure set at once"), but a comment is not verification. Requires
`DARTMOUTH_CHAT_API_KEY`; the check belongs in `tests/real_call/` alongside the SC-008 matrix.
**If the real call fails, STOP and escalate** — the decision flips to migrating the call site to
`qwen3-vl` as a sanctioned behavior delta (the D1 runner-up), which would also require adding
`qwen3-vl` to the conftest offline snapshot.

**Exact test fallout of the version bump + attribution** (located, not predicted):

|test|change|
|-|-|
|`tests/unit/test_model_selection_policy.py:20`|`CAPABILITY_POLICY.version == SELECTION_POLICY_VERSION == 1` → `== 2`|
|`tests/unit/test_model_selection_select.py:488`|`chain.selection_policy_version == 1` → `== 2`|
|`tests/unit/test_model_selection_select.py:271`|the `vision`-profile selection: leader becomes `qwen.qwen3.5-122b` with `qwen3-vl:32b` as the tier-2 peer|

`test_model_selection_policy.py:47-48` (`qwen3-vl` is vision-only, NOT `deep`) is **unaffected** —
adding `vision` to `qwen3.5` does not change `qwen3-vl`'s attribution. `test_model_selection_select.py:264`
("qwen3-vl … attributed ONLY vision → excluded" from a text chain) also stays true.

## §5 — Direct pins (43 rows) + two reclassifications

`_walker_route` / `reasoning_chat` / `chat_with_model_fallback` gain a
`profile: str = "standard_generation"` parameter threaded to `route_chat` (today the profile is
hardcoded at `router.py:320` and `:435`). The default preserves every unmigrated caller's behavior.
Then the 35 `model_id_literal` + 8 remaining `module_constant` rows drop `model=` and pass `profile=`:

|intent|profile|sites|
|-|-|-|
|extraction / classification / structured parse|`cheap_structured`|`claims/extract.py`, `claims/resolve.py`, `fill/extract.py`, `fill/service.py`, `librarian/query_extractor.py`, `librarian/math_classifier.py`, `librarian/data_source_discovery.py`, `execution/data_source.py`, `tools/summarize.py:248`|
|review / entailment / triage / judgment|`deep_review`|`grounding/entailment.py`, `agents/grounding_guard.py`, `convergence/triage.py`, `convergence/engine.py:400`, `librarian/relevance_judge.py`, `agents/task_verifier.py`, `agents/living_document.py`|
|revision of code + specs|`deep_code`|the `convergence/revisers/*` family (implementer, paper_implement, spec, paper_spec, plan, tasks, flesh_out)|
|figure review|`vision`|`paper_reprocess/preprint_figures.py`|
|persona generation|`standard_generation`|`agents/personality.py:68` (`MODEL_NAME`)|

**Two manifest rows are misclassified as `migration_target` and become `canonical_layer`** (same
status as `_REASONING_MODELS`):

- `backends/local.py:37` `list_models` → `Qwen/Qwen2.5-3B-Instruct` is the local backend **declaring
  its own inventory**. It is a snapshot *input*, not a selection pin — deleting it would blind the
  composite snapshot (SC-010). Requires an `inventory.py` classification change + manifest regen.
- `tools/summarize.py:45` `_MODEL_BUDGETS` is a model→context-budget lookup table, not a selection
  pin. Rather than reclassify, **delete it and read `policy.max_context_tokens(family)`** — the SSoT
  win hiding in this row (Constitution I). This is the one §5 change with real behavior surface:
  assert the resolved budgets match the current table for the models it covers.

`backends/dartmouth.py:510` `KNOWN_FREE_MODELS` stays this slice (Slice 8 deletes it); Slice 7 only
removes `test_config_consistency`'s dependency on it (§6).

## §6 — Tests: US5 AC1 + AC4, and run-log attribution

### AC1 (new, binding)
`tests/unit/` — for all 53 LLM agents, under the fixed migration snapshot, assert
`select(build_requirement(entry.profile, …), snapshot).candidates[0].model_ref.model_id ==
"qwen.qwen3.5-122b"`; assert `paper_publisher` is exempt (never reaches selection). This is the
all-LLM-agents primary-preservation test US5 deferred to this slice.

### AC4 (rewrite `tests/unit/test_config_consistency.py`)
Drops the `KNOWN_FREE_MODELS` (`backends/dartmouth.py`) and `MODEL_FALLBACKS` (`backends/router.py`)
imports at lines 25-26 and validates **capability profiles**:

|current test|becomes|
|-|-|
|`test_registry_models_are_free_unless_paid_opt_in` (:59)|every agent's `profile` is canonical; each profile's chain under the fixed snapshot is free-only unless the agent sets `paid_opt_in`|
|`test_model_fallback_chains_are_free` (:77)|the **policy** admits no paid family except the sanctioned `claude-haiku-4-5`|
|`test_every_llm_registry_model_has_a_fallback_chain` (:95)|every profile resolves to ≥2 candidates (the outage-stranding guard, re-expressed)|
|`test_readme_model_names_match_registry` (:134)|re-pointed at the policy table — the registry no longer names models|

**`README.md`'s "Models & cost" section must be updated in the same commit** (CLAUDE.md: docs change
with code; the test above enforces it).

### Run-log attribution (D4)
`RunLogEntry.backend` → `BackendName | None`, `model_name` → `str | None`, plus a validator requiring
both non-`None` when `outcome is Outcome.SUCCESS`. `agents/base.py:137-138` stops seeding from the
registry and records only what actually happened (the success path already overwrites from
`response.backend` / `response.model` at `base.py:162-163`).

Verified safe: `state/runlog.py:237` filters `entry.outcome is not Outcome.SUCCESS` **before**
building paper authorship, and `pipeline/authors.py:207-213` already null-guards both fields.
`ReviewRecord` (`types.py:618`) already uses this exact nullable+validator idiom, so it is the
codebase's own convention rather than a new one. The rejected alternative — a sentinel like
`"unresolved:deep_review"` plus a fabricated `BackendName.DARTMOUTH` — would write a model that never
ran and a backend never contacted into a field feeding paper authorship, harmless only by accident of
a downstream filter.

## §7 — Task sequencing (each independently green + committed)

|#|task|clears|
|-|-|-|
|1|`exclude_leader` in `types.RequirementOverrides` + `select()` + `execution_status` / `graph.py` de-parameterization|§3|
|2|**Real-call vision verification** → policy `vision` attribution + `SELECTION_POLICY_VERSION` 2 (STOP + escalate on failure)|§4|
|3|`AgentRegistryEntry` schema + all 54 `registry.yaml` entries + `SlashCommandContext`|§1, 161+3 rows|
|4|the 91 `field_consumer` sites|§1|
|5|walker `profile` param + the 43 direct pins|§5|
|6|`_MODEL_BUDGETS` → `policy.max_context_tokens`; `local.py` reclassification in `inventory.py`|§5|
|7|`RunLogEntry` nullable + validator + `base.py` attribution|§6|
|8|AC1 test + `test_config_consistency` rewrite + README|§6|
|9|manifest regeneration + full non-slow suite + zero surviving `owning_slice==7` rows|all|

Manifest regenerates after every pin-moving task (frozen-drift test), not only at task 9.

## Risks

|risk|mitigation|
|-|-|
|Vision real-call verification fails|Task 2 is gated and STOPS the slice; D1's runner-up (migrate to `qwen3-vl` + snapshot fixture) is pre-designed.|
|`max_candidates=4` truncates the paid tail for 37 newly-assigned agents|§2.1 raises it to 8 on the text profiles; assert chain length ≥ free-peers + paid tail against a composite (not offline) snapshot.|
|Deleting `default_backend` breaks a test double constructing `AgentRegistryEntry`|267 `test_double` manifest rows are the inventory; the schema change is a load-time failure, so breakage is loud, not silent.|
|`SELECTION_POLICY_VERSION` bump invalidates a stored golden|Goldens are model-ID projections (SC-007), not byte-equal objects; update the vision golden only.|
|A profile mis-assignment goes unnoticed|Leaders are all `qwen3.5` under the fixed snapshot, so AC1 cannot catch a wrong-but-plausible profile. Accepted: assignment is reviewed by a spec/quality reviewer per task, and the tail-length assertion in §2.1 catches capability mistakes.|

## Definition of done (Slice 7)

Zero surviving `owning_slice==7` manifest rows; `AgentRegistryEntry` carries `profile` and no model
ids; `exclude_leader` replaces the tier-1 model-id exclusion; US5 AC1 + AC4 landed;
`test_config_consistency` free of `KNOWN_FREE_MODELS`/`MODEL_FALLBACKS`; README consistent; full
non-slow suite green; vision real-call verified. **Then** Slice 8.
