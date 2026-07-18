# Slice 6 design — execution-tier ladder → escalating requirement constraints (issue #1242, spec 026)

**Status:** DESIGN APPROVED-IN-PROGRESS (maintainer reviewed 2026-07-18, two decisions locked).
**Branch:** `026-model-selection-consolidation`. **Base:** the Slice-5 stack (HEAD `5223f78e66`).
**Predecessor handoff:** [2026-07-17-issue-1242-slice5-handoff.md](2026-07-17-issue-1242-slice5-handoff.md).

## Goal

Migrate the one remaining slice-6 manifest target — `FREE_MODEL_TIERS` at
[execution_status.py:63](../src/llmxive/state/execution_status.py#L63), a hardcoded **model-id
ladder** `("", "openai.gpt-oss-120b")` — into **escalating requirement constraints** applied
through `route_chat`/`select`, per spec US6 / FR-013. Remove the model-id literal; keep model
knowledge in the policy/catalog layer.

**Approach (maintainer decision):** thread the escalation constraints through the agent
interface (`SlashCommandContext` → speckit agent + convergence reviser/reviewer → `route_chat`),
so `select()` applies them directly. NO model-id promotion via `caller_model`. This is the
"bigger, less isolated slice"; it deliberately does NOT do Slice 7's per-agent base-*profile*
work (the `AgentRegistryEntry` schema migration) — it adds only the orthogonal escalation-
*override* channel on top of the existing base profile.

## What is preserved (unchanged)

- The persisted integer `model_tier` state machine: `model_tier`, `bump_model_tier`,
  `next_usable_tier`, `reset_fix_loop`, `record`, `total_attempts`, `replan_rounds`, the offload
  sub-record, `MAX_EXECUTION_FIX_ROUNDS`, `MAX_REPLAN_ROUNDS`.
- Graph routing: escalate → stay `IN_PROGRESS`; exhaust all tiers → deterministic re-plan;
  never `human_input_needed`. The `free_only` fabrication guard (a fabrication failure never
  climbs onto a paid rung).
- Free→paid ordering; paid opt-in + credit guard; the two-tier advancement bar.

## Maintainer review — blocking issues fixed in this design

The first design draft had three real defects the maintainer caught. All fixed here:

1. **`{}` is not "free-only."** `route_chat` derives `allow_paid` from the snapshot opt-in when
   the caller passes `None` ([route.py:174](../src/llmxive/model_selection/route.py#L174)):
   `allow_paid_eff = snap.credit.paid_opt_in if allow_paid is None else allow_paid`. So an empty
   override lets tier 0 spend when opt-in is on. **Worse:** a raw `{"allow_paid": False}` mapping
   would `TypeError` — `route_chat` already passes `allow_paid=allow_paid_eff` explicitly to
   `build_requirement(..., **requirement_overrides)`, so `allow_paid` in the mapping collides
   ("multiple values for keyword argument"). → **every rung (and the fail-safe) emits
   `allow_paid` explicitly, routed to the `route_chat` PARAMETER via a typed contract, never a
   raw dict.**
2. **`allow_paid=True` is not an escalation.** Under the v1 policy (`qwen3.5`=tier3,
   `gemma-4`/`gpt-oss`=tier2, `qwen2.5`=tier1, `claude-haiku`=**tier3 paid**), a paid rung of
   `allow_paid=True, exclude={default}` yields `[gemma-4, gpt-oss, local, claude]` under
   mandatory free-before-paid — gemma leads, claude never runs; 12 "paid" fix-rounds served by
   free. And `min_quality_tier` can't fix it: claude-haiku and qwen3.5 are **both tier 3**, so
   `min_quality_tier=3` leaves `{qwen3.5 free, claude paid}` → free-first → qwen (unless the
   excluded default *is* qwen3.5 — fragile). → **add a `require_paid` cost-class field
   (decision).**
3. **Model-id env var reinterpreted as a count** was rejected. → **new
   `LLMXIVE_EXECUTION_PAID_ESCALATION` boolean with a deprecation path (decision).**

Also fixed per review: corrupt/out-of-range `model_tier` resolves to **tier 0 / free-only**,
NEVER clamps to the last (paid) rung (clamping would broaden spending authority). Multiple
identical paid rungs are collapsed to one. `paid_tier_usable()` is a coarse, cache-bypassing,
fail-closed pre-check documented as distinct from select()/execute() enforcement.

## Locked decisions (maintainer, 2026-07-18)

- **Paid mechanism = `require_paid`.** Add `require_paid: bool = False` to `ModelRequirement`
  (FR-003 contract addition) + one line in select's paid guard. Robust regardless of the agent's
  registered default; fails closed when paid is unavailable.
- **Paid config = `LLMXIVE_EXECUTION_PAID_ESCALATION` bool + deprecation.** `=1` enables the
  single paid rung. Legacy `LLMXIVE_EXECUTION_PAID_TIERS`, if set nonempty, collapses to one paid
  rung and logs a deprecation warning that model-ids are no longer honored (documented removal).

## The design

### A. `ModelRequirement.require_paid` (contract addition, `model_selection/types.py` + `select.py`)

```python
# ModelRequirement gains (FR-003):
require_paid: bool = False   # this rung REQUIRES a paid model — exclude all free candidates
```
select's paid guard (after `is_free` is known) gains one line:
```python
if requirement.require_paid and is_free:
    continue   # a require_paid rung excludes every free candidate → paid leads (or fail closed)
```
`require_paid=True` is only meaningful with `allow_paid=True`; the paid rung sets both. When paid
is not admissible (opt-in off / stale credit / over per-call ceiling), select finds NO eligible
candidate → `ModelUnavailable` (fail closed) — the correct outcome for a rung that demands paid.
Spec FR-003 + the `ModelRequirement` component description get the new field; bump nothing in the
policy version (this is a requirement field, not a policy change).

### B. The escalation ladder (`state/execution_status.py`)

Replace `FREE_MODEL_TIERS: tuple[str, ...]` with a ladder of constraint presets:

```python
@dataclass(frozen=True)
class TierConstraint:
    """One escalation rung as REQUIREMENT overrides (never a model id)."""
    allow_paid: bool = False
    exclude_registered_default: bool = False   # -> exclude_models={default} at resolve time
    require_paid: bool = False
    max_credits: int | None = None

    @property
    def is_paid(self) -> bool:
        return self.allow_paid or self.require_paid

    def to_overrides(self, default_model: str) -> "RequirementOverrides":
        return RequirementOverrides(
            allow_paid=self.allow_paid,                       # ALWAYS explicit (incl. False)
            require_paid=self.require_paid,
            exclude_models=(frozenset({default_model})
                            if self.exclude_registered_default else frozenset()),
            max_credits=self.max_credits,
        )
```

Ladder construction (`model_tier_ladder() -> tuple[TierConstraint, ...]`):
- tier 0 → `TierConstraint(allow_paid=False)` — base free chain; registered default leads.
- tier 1 → `TierConstraint(allow_paid=False, exclude_registered_default=True)` — free second
  opinion; select leads with the policy's next-best free (gemma-4 under v1).
- tier 2 → `TierConstraint(allow_paid=True, require_paid=True)` — **iff** paid escalation enabled.

Length: 2 (free-only, the default) or 3 (paid enabled). At most one paid rung; duplicates
collapsed. `LLMXIVE_EXECUTION_PAID_ESCALATION` truthy (or the deprecated
`LLMXIVE_EXECUTION_PAID_TIERS` nonempty, with a one-time warning) appends the single paid rung.

Function changes:
- `execution_model_override(...)` (returned a model-id) → **removed**. Replaced by
  `tier_overrides(project_id, *, default_model, repo_root) -> RequirementOverrides`, resolving the
  CURRENT tier's `TierConstraint`. Corrupt/out-of-range tier → `TierConstraint(allow_paid=False)`
  free-only fail-safe (NOT the last rung).
- `tier_model(tier)` (model-id) → `tier_constraint(tier) -> TierConstraint`, with the same
  free-only fail-safe for out-of-range.
- `paid_tier_usable()` → model-agnostic: `paid_opt_in_enabled()` AND a **fresh, cache-bypassing**
  credit-headroom observation that is **finite and > 0**; fail closed on any error. `next_usable_tier`
  skips a rung when `constraint.is_paid` and (`free_only` OR not `paid_tier_usable()`).
- `EXECUTION_PAID_TIERS_ENV` → `PAID_ESCALATION_ENV = "LLMXIVE_EXECUTION_PAID_ESCALATION"`; a
  private `_legacy_paid_tiers_set()` handles the deprecated var + warning.

**Layered paid enforcement (documented):** `paid_tier_usable()` = coarse "paid globally enabled
+ some daily headroom" state-machine filter · `select()` = per-call worst-case cost ≤ ceiling ·
`execute()` = authoritative fresh reservation. The coarse check can pass while select admits no
paid candidate (per-call cost too high) → the rung fails closed rather than silently re-serving
free.

### C. Typed override contract (`model_selection/types.py` or `route.py`)

```python
@dataclass(frozen=True)
class RequirementOverrides:
    allow_paid: bool | None = None        # -> route_chat's allow_paid PARAM (None = snapshot-derived)
    require_paid: bool = False            # -> ModelRequirement.require_paid
    exclude_models: frozenset[str] = frozenset()
    max_credits: int | None = None
```
Frozen/immutable → safe to share read-only across the panel `ThreadPoolExecutor`; fixed field set
→ no key collisions with routing-control params (`profile`, `max_tokens`, `snapshot`,
`ledger_repo`, `backend_factory`). `route_chat` gains one `overrides: RequirementOverrides | None`
param and centralizes the mapping in ONE place: `allow_paid` → the `allow_paid_eff` derivation;
`require_paid`/`exclude_models`/`max_credits` → merged into `build_requirement`. The legacy
`**requirement_overrides` catch-all on `route_chat` is REMOVED (typed replaces untyped).

### D. Threading (rides parallel to the existing `model=`; default `None` everywhere)

- `backends/router.py`: `_walker_route`, `chat_with_fallback`, `chat_with_model_fallback`,
  `reasoning_chat` each gain `overrides: RequirementOverrides | None = None`, forwarded to
  `route_chat(overrides=...)`.
- `speckit/slash_command.py`: `SlashCommandContext` gains `requirement_overrides:
  RequirementOverrides | None = None`; `SlashCommandAgent.run()` passes it into its
  `chat_with_fallback(overrides=...)` call.
- `convergence/reviewspecs.py`: the ~10 `build_*_reviewspec` + `_wire_live_panel` +
  `llm_reviewer.build_panel` + `LLMReviewer.__init__` (stores `self._overrides`) thread the
  overrides; `_call_backend` passes `overrides=self._overrides`. **Revisers get `_overrides` at
  CONSTRUCTION** (each `build_*_reviewspec` sets it on the reviser object it builds — not only
  the panel side); `invoke_reviser_backend` reads `getattr(reviser, "_overrides", None)` and
  passes it to `reasoning_chat(overrides=...)`.
- The 7 speckit command call sites (`clarify_cmd`, `paper_clarify_cmd`, `plan_cmd`,
  `paper_plan_cmd`, `paper_implement_cmd`, `paper_tasks_cmd`, `_tasker_engine_bridge`) pass
  `requirement_overrides=ctx.requirement_overrides` into their `build_*_reviewspec(...)`.

### E. Graph rewiring (`pipeline/graph.py`) — 3 sites

- Dispatch (~776): stop overloading `ctx.default_model` with the tier model-id. Set
  `default_model=entry.default_model` (registry default — Slice 7's concern) and
  `requirement_overrides=execution_status.tier_overrides(project.id,
  default_model=entry.default_model, repo_root=repo)` on the `SlashCommandContext`. Applies to
  BOTH the exec-fix implementer (`IN_PROGRESS`) and the doc-stage panels (`_STAGE_PANEL_LABEL`).
- Escalation sites (~1534 panel, ~1785 exec-fix): `bump_model_tier`/`reset_fix_loop` unchanged;
  the log lines calling `tier_model(new_tier)` switch to a stable `TierConstraint` description
  (e.g. `"tier 2 (paid, require_paid)"`).

### F. Spec + manifest

- `specs/026.../spec.md`: record the tier-1 `gpt-oss → gemma-4` shift as an explicit **sanctioned
  migration delta** under US6/SC-007; add `require_paid` to FR-003 + the `ModelRequirement`
  component; note the `LLMXIVE_EXECUTION_PAID_ESCALATION` config + deprecation. Update the golden
  from pinned gpt-oss to policy-selected gemma-4.
- Regenerate the migration manifest (`python -m llmxive.model_selection.inventory`) — the
  `FREE_MODEL_TIERS` slice-6 row drops with NO new model pins introduced (frozen drift test
  enforces the regen). Update `test_model_selection_inventory.py:323`.

## Behavior deltas (intended, sanctioned)

1. **tier-1 free second opinion**: pinned `openai.gpt-oss-120b` → policy-selected next-best free
   (gemma-4 under v1). The point of "not another list of model ids."
2. **paid escalation genuinely reaches paid** (`require_paid`) instead of being buried by
   free-before-paid — a *correctness fix* over the accidental prior behavior of the naive draft;
   matches the OLD model-override intent (the configured paid model ran first).
3. **paid config**: `LLMXIVE_EXECUTION_PAID_TIERS` (model-id list) → `LLMXIVE_EXECUTION_PAID_ESCALATION`
   (bool), old var deprecated with a one-time warning.

## Required tests (maintainer list — all adopted)

- `tier_overrides`/`tier_constraint`: tier 0 sets `allow_paid=False` even when snapshot opt-in is
  true; tier 1 sets `allow_paid=False`; invalid/corrupt/out-of-range tier resolves free-only.
- Fabrication (`free_only=True`) never reaches a `is_paid` rung.
- Tier 1 excludes the default across the WHOLE chain (fixed snapshot: tier 0 = `qwen → gemma-4 →
  gpt-oss → local`; tier 1 = `gemma-4 → gpt-oss → local`), leader is gemma-4.
- **AC1 / Independent Test**: each tier's overrides fed through `select()` under a fixed snapshot +
  credit state reproduce the free→paid ordering (all free before any paid).
- A paid rung reaches a paid candidate on *semantic* free exhaustion (require_paid), not only when
  every free backend is unavailable.
- Multiple configured paid rungs are collapsed/rejected (never duplicated).
- Missing/low/non-finite headroom skips paid rungs; per-call cost too high still fails closed in
  `select()`.
- Override propagation reaches all five hops: direct SlashCommand exec, every reviewspec builder,
  panel reviewers **concurrently across the thread pool** (each gets the same immutable value, no
  cross-review mutation), revisers, and the final `route_chat`.
- Existing `model_tier` / reset / re-plan / fabrication routing tests (`test_execution_exhaustion_flow`,
  `test_execution_replan_cap`, `test_convergence_kickback_flow`) unchanged in OUTCOME; only their
  model-id-literal assertions become constraint assertions.
- Manifest regeneration removes `FREE_MODEL_TIERS` and introduces no new model pins.

## Files touched (change map)

| file | change |
|-|-|
|`model_selection/types.py`|`ModelRequirement.require_paid`; `RequirementOverrides` dataclass|
|`model_selection/select.py`|one-line `require_paid` free-exclusion in the paid guard|
|`model_selection/route.py`|`overrides: RequirementOverrides` param; centralized mapping; drop `**requirement_overrides`|
|`state/execution_status.py`|`TierConstraint`; `tier_overrides`/`tier_constraint`; `model_tier_ladder`→constraints; `paid_tier_usable` model-agnostic; `PAID_ESCALATION_ENV` + legacy deprecation; remove `FREE_MODEL_TIERS`/`execution_model_override`/`tier_model`|
|`backends/router.py`|`overrides` param on the 4 walkers → `route_chat`|
|`speckit/slash_command.py`|`SlashCommandContext.requirement_overrides`; `run()` forwards it|
|`convergence/reviewspecs.py`|thread `requirement_overrides` through builders/`_wire_live_panel`; set reviser `_overrides` at construction|
|`convergence/llm_reviewer.py`|`build_panel`/`LLMReviewer` carry+forward `_overrides`|
|`convergence/revisers/_self_consistency.py`|`invoke_reviser_backend` reads `_overrides` → `reasoning_chat`|
|`speckit/{clarify,plan,paper_clarify,paper_plan,paper_implement,paper_tasks}_cmd.py`, `_tasker_engine_bridge.py`|pass `ctx.requirement_overrides` into `build_*_reviewspec`|
|`pipeline/graph.py`|dispatch sets `requirement_overrides`; log lines describe the constraint|
|`specs/026.../spec.md`, `migration_manifest.{json,md}`|FR-003 + US6/SC-007 delta; regen manifest|
|`tests/...`|new tests above; convert model-id assertions to constraint assertions|

## Delivery order (TDD per slice; commit after each green step)

1. `require_paid` field + select gate (+ unit tests: require_paid excludes free; fails closed).
2. `RequirementOverrides` typed contract + `route_chat` `overrides=` param + centralized mapping
   (+ tests incl. the `allow_paid`-collision regression).
3. `execution_status` ladder → `TierConstraint`/`tier_overrides` + `PAID_ESCALATION` env +
   deprecation (+ the tier/fabrication/corrupt-state tests; convert the exhaustion-flow assertions).
4. Walker `overrides` threading (`router.py`) (+ walker→route_chat propagation tests).
5. Speckit + convergence threading (context, agent, reviewspecs, reviewer, reviser) (+ the
   5-hop + concurrent-reviewer propagation tests).
6. Graph rewiring (dispatch + escalation logs) (+ the routing tests stay green).
7. Spec delta + manifest regen (+ inventory test update; frozen drift test green).
8. Full non-slow backstop; ruff; `git diff --check`; regenerate the resume handoff note.
