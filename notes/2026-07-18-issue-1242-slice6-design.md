# Slice 6 design — execution-tier ladder → escalating requirement constraints (issue #1242, spec 026)

**Status:** DESIGN APPROVED (maintainer round-1 + round-2 review 2026-07-18; two decisions locked,
four round-2 clarifications folded in — §"Round-2 clarifications"). Ready to implement.
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

## Round-2 clarifications (maintainer, 2026-07-18) — folded into the sections below

These are binding refinements, not new decisions. They are specified here in one place and
reflected inline in §A–§F.

1. **`allow_paid` precedence (route_chat param vs `overrides.allow_paid`).** No silent precedence.
   If BOTH the standalone `allow_paid` param AND `overrides.allow_paid` are non-`None`, `route_chat`
   **raises `ValueError`** ("allow_paid supplied both directly and through overrides"). Resolution
   order otherwise: `overrides.allow_paid` (if non-None) → standalone `allow_paid` (if non-None) →
   `snapshot.credit.paid_opt_in`. Tier-generated overrides always carry a concrete boolean, so
   every escalation rung is explicit; non-tier callers keep using the standalone param during
   migration. The standalone param is deleted once all callers use the typed contract (Slice 8-ish).

2. **Overrides COMPOSE with (never replace) the base profile — additive/tightening merge.**
   `route_chat` builds the base requirement from the profile FIRST, then merges overrides:
   `exclude_models` = **union**; `max_credits` = **tighter non-None** (`min` when both set, else the
   set one); `require_paid` = `base.require_paid OR overrides.require_paid`; `allow_paid` = the
   resolved tier authority (rule 1); future set-valued fields **union** unless documented. This
   matters for Slice 7, when per-agent profiles may already carry exclusions / tighter ceilings —
   escalation must tighten, not erase policy. Shape:
   ```python
   base = build_requirement(profile, budget, independence_against=...)
   req = replace(base,
       allow_paid=resolved_allow_paid,
       require_paid=base.require_paid or ov.require_paid,
       exclude_models=base.exclude_models | ov.exclude_models,
       max_credits=_tighter(base.max_credits, ov.max_credits))
   ```
   Test with a synthetic base profile that already has an exclusion + a `max_credits`.

3. **Paid-headroom arithmetic lives in `backends/credits.py`, not `execution_status.py`
   (Constitution I).** Add a canonical helper — `fresh_paid_headroom_available() -> tuple[bool, str]`
   (or `effective_headroom(balance) -> float`) — that: fetches a **cache-bypassing** balance,
   applies the canonical `budget_fraction`, **rejects non-finite** spend/max_budget/fraction/cap/
   headroom, requires opt-in, returns `False` when headroom `<= 0`, and fails closed on any
   acquisition error. `paid_tier_usable()` **delegates** to it — it owns no financial arithmetic.
   Keeps selection / execution / escalation on ONE cap definition.

4. **Exact env precedence + parsing.** (a) If `LLMXIVE_EXECUTION_PAID_ESCALATION` is **present**:
   recognized-true → enable one rung; recognized-false (incl. an explicit `=0`) → disable; invalid
   value → warn + **fail closed** (disabled); the legacy var is **ignored entirely**. (b) Else if
   legacy `LLMXIVE_EXECUTION_PAID_TIERS` is nonempty → enable exactly one rung, emit **one**
   deprecation warning, ignore all listed model-ids. (c) Else disabled. An explicit new `=0` MUST
   override a lingering legacy list (so an operator can actually turn paid OFF). Parse booleans with
   the established `{"1","true","yes","on"}` idiom (as `credits.py:129` does); optionally extract a
   shared `env_bool()` helper (Constitution I — low-priority follow-up). Test matrix: true / false /
   `0` / blank / invalid / legacy-only / both-set / duplicate legacy values / warn-once.

### Additional recommendations (also folded in)

- **Corrupt `model_tier` validated completely.** Route the persisted `model_tier` through
  `_nonneg_int` (which excludes `bool` — `isinstance(True, int)` is `True`!). Today `model_tier`
  (execution_status.py:143) and its sibling `fix_rounds` (:136) use a bool-permissive check, so a
  persisted `true` reads as tier/round `1`. Fix both (handle-issues-as-you-go). Then `tier_constraint`
  clamps any valid-but-out-of-range index to **tier 0 / free-only** (never the last paid rung). Test:
  negative int, `bool`, `float`, numeric string, huge int, missing → all resolve to tier 0/free-only
  except valid in-range ints.
- **Reviser overrides are a DECLARED field**, not a dynamically-attached attribute (dynamic attrs
  break on frozen/slotted classes and are lost on clone). Add `_overrides` to the reviser
  base / shared construction path so every concrete reviser carries it explicitly. The concurrency
  test exercises the REAL `build_*_reviewspec → panel → reviewer` path, not `build_panel()` in
  isolation.
- **`require_paid=True, allow_paid=False` has an explicit contract**, not silent reinterpretation:
  it **fails closed with `ModelUnavailable`** carrying an explicit reason (a require-paid requirement
  with paid disabled admits no candidate). Tested.

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
**Explicit contract for the nonsensical combo `require_paid=True, allow_paid=False`:** it is NOT
silently reinterpreted — it fails closed with `ModelUnavailable` carrying an explicit reason
(require-paid excludes every free candidate AND paid is inadmissible → zero candidates). Tested
directly. Spec FR-003 + the `ModelRequirement` component description get the new field; bump
nothing in the policy version (this is a requirement field, not a policy change).

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
  CURRENT tier's `TierConstraint`. The persisted `model_tier` is read through `_nonneg_int` (which
  excludes `bool`), and any valid-but-out-of-range index → `TierConstraint(allow_paid=False)`
  free-only fail-safe (NOT the last rung).
- `tier_model(tier)` (model-id) → `tier_constraint(tier) -> TierConstraint`, with the same
  free-only fail-safe for out-of-range / corrupt.
- **Bool-safety bug fix (handle-issues-as-you-go):** `model_tier` (:143) and `fix_rounds` (:136)
  currently use `isinstance(t, int)` WITHOUT excluding `bool`, so a persisted `true` reads as `1`.
  Route both through `_nonneg_int` (:310, already bool-safe).
- `paid_tier_usable()` → model-agnostic and **delegates** to a NEW canonical
  `backends/credits.fresh_paid_headroom_available() -> tuple[bool, str]` (Constitution I: no
  financial arithmetic in `execution_status.py`). That helper: fetches a **cache-bypassing**
  balance, applies the canonical `budget_fraction`, rejects **non-finite** spend/max_budget/
  fraction/cap/headroom, requires opt-in, returns `False` when headroom `<= 0`, and fails closed on
  any acquisition error. `next_usable_tier` skips a rung when `constraint.is_paid` and (`free_only`
  OR not `paid_tier_usable()`).
- `EXECUTION_PAID_TIERS_ENV` → `PAID_ESCALATION_ENV = "LLMXIVE_EXECUTION_PAID_ESCALATION"`. Env
  precedence is EXACT (Round-2 #4): new var present wins (true→on, false/`0`/invalid→off, legacy
  ignored; invalid warns + fails closed); else legacy nonempty → one rung + one deprecation warning
  (model-ids ignored); else off. A private `_paid_escalation_enabled()` owns this; booleans parsed
  with the `{"1","true","yes","on"}` idiom.

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
param and centralizes the mapping in ONE place. The legacy `**requirement_overrides` catch-all on
`route_chat` is REMOVED (typed replaces untyped; convert any existing `route.py` tests exercising
the kwarg path).

**`allow_paid` precedence (Round-2 #1):** if BOTH the standalone `allow_paid` param and
`overrides.allow_paid` are non-`None` → `raise ValueError`. Else `allow_paid_eff` =
`overrides.allow_paid` (if set) → standalone `allow_paid` (if set) → `snapshot.credit.paid_opt_in`.

**Compose with the base profile — additive/tightening, never replace (Round-2 #2):** `route_chat`
builds the base requirement from the profile first, then `replace`s with the MERGE:
```python
base = build_requirement(profile, call_budget, independence_against=independence_against)
req  = replace(base,
    allow_paid=allow_paid_eff,
    require_paid=base.require_paid or ov.require_paid,
    exclude_models=base.exclude_models | ov.exclude_models,   # union
    max_credits=_tighter(base.max_credits, ov.max_credits))    # tighter non-None (min)
```
`_tighter(a, b)` = the set one when only one is set, else `min(a, b)`. Future set-valued override
fields union unless documented otherwise. (When `overrides is None`, `req = base` and today's
snapshot-derived `allow_paid` behavior is unchanged.)

### D. Threading (rides parallel to the existing `model=`; default `None` everywhere)

- `backends/router.py`: `_walker_route`, `chat_with_fallback`, `chat_with_model_fallback`,
  `reasoning_chat` each gain `overrides: RequirementOverrides | None = None`, forwarded to
  `route_chat(overrides=...)`.
- `speckit/slash_command.py`: `SlashCommandContext` gains `requirement_overrides:
  RequirementOverrides | None = None`; `SlashCommandAgent.run()` passes it into its
  `chat_with_fallback(overrides=...)` call.
- `convergence/reviewspecs.py`: the ~10 `build_*_reviewspec` + `_wire_live_panel` +
  `llm_reviewer.build_panel` + `LLMReviewer.__init__` (stores `self._overrides`) thread the
  overrides; `_call_backend` passes `overrides=self._overrides`. **Revisers carry `_overrides` as a
  DECLARED field** on the reviser base / shared construction path (NOT a dynamically-attached
  attribute — that breaks on frozen/slotted classes and is lost on clone), set when each concrete
  reviser is constructed in `build_*_reviewspec` (not only the panel side); `invoke_reviser_backend`
  reads it and passes it to `reasoning_chat(overrides=...)`.
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
  true; tier 1 sets `allow_paid=False`.
- **Corrupt `model_tier` full matrix** → all resolve to tier 0 / free-only EXCEPT valid in-range
  ints: negative int, `bool` (`True`/`False`), `float`, numeric string, huge int, missing.
- Fabrication (`free_only=True`) never reaches a `is_paid` rung.
- **Explicit tier golden** (fixed snapshot, default = qwen3.5), stated per-tier — not just "free
  before paid":
  - tier 0: `qwen → gemma-4 → gpt-oss → local`
  - tier 1: `gemma-4 → gpt-oss → local` (default excluded across the WHOLE chain; leader gemma-4)
  - tier 2: `claude` — **paid-only** (require_paid excludes all free; "all free before paid" is
    vacuously true here, so assert the paid-only leader explicitly).
- **AC1 / Independent Test**: each tier's overrides fed through `select()` under a fixed snapshot +
  credit state reproduce the above free→paid ordering.
- `require_paid=True, allow_paid=False` fails closed with `ModelUnavailable` (explicit reason).
- **`allow_paid` precedence**: both standalone param + `overrides.allow_paid` set → `ValueError`;
  otherwise overrides wins, then standalone, then snapshot opt-in.
- **Compose-with-base-profile merge**: synthetic base profile carrying an existing `exclude_models`
  entry + a `max_credits` → overrides UNION the exclusions and take the TIGHTER `max_credits`
  (neither erased); `require_paid` is `base OR override`.
- **Env precedence matrix**: `LLMXIVE_EXECUTION_PAID_ESCALATION` true / false / `0` / blank /
  invalid(→warn+off) / legacy-`PAID_TIERS`-only(→one rung + one warning) / both-set(new wins,
  legacy ignored) / duplicate legacy values / warn-emitted-once. Explicit new `=0` overrides a
  lingering legacy list.
- **Canonical headroom helper** (`fresh_paid_headroom_available`): opt-in off → False; non-finite
  spend/max_budget/fraction → False (fail closed); headroom `<= 0` → False; acquisition error →
  False; healthy → True. `paid_tier_usable` delegates (no arithmetic of its own).
- A paid rung reaches a paid candidate on *semantic* free exhaustion (require_paid), not only when
  every free backend is unavailable.
- Multiple configured paid rungs are collapsed/rejected (never duplicated).
- Per-call cost too high still fails closed in `select()`.
- Override propagation reaches all five hops: direct SlashCommand exec, every reviewspec builder,
  panel reviewers **concurrently across the thread pool** exercised through the REAL
  `build_*_reviewspec → panel → reviewer` path (not `build_panel` in isolation) — each reviewer
  gets the same immutable value, no cross-review mutation — revisers (declared `_overrides` field),
  and the final `route_chat`.
- Existing `model_tier` / reset / re-plan / fabrication routing tests (`test_execution_exhaustion_flow`,
  `test_execution_replan_cap`, `test_convergence_kickback_flow`) unchanged in OUTCOME; only their
  model-id-literal assertions become constraint assertions.
- Manifest regeneration removes `FREE_MODEL_TIERS` and introduces no new model pins.

## Files touched (change map)

| file | change |
|-|-|
|`model_selection/types.py`|`ModelRequirement.require_paid`; `RequirementOverrides` dataclass|
|`model_selection/select.py`|one-line `require_paid` free-exclusion in the paid guard; explicit `ModelUnavailable` reason for `require_paid ∧ ¬allow_paid`|
|`model_selection/route.py`|`overrides: RequirementOverrides` param; `allow_paid` precedence + ValueError; compose/tighten merge with the base profile; drop `**requirement_overrides`|
|`backends/credits.py`|NEW canonical `fresh_paid_headroom_available()` (cache-bypassing, non-finite-rejecting, opt-in-gated, fail-closed)|
|`state/execution_status.py`|`TierConstraint`(+`is_paid`); `tier_overrides`/`tier_constraint`; `model_tier_ladder`→constraints; `paid_tier_usable` delegates to credits helper; `_paid_escalation_enabled()` + exact env precedence + legacy deprecation; `model_tier`/`fix_rounds` bool-safety via `_nonneg_int`; remove `FREE_MODEL_TIERS`/`execution_model_override`/`tier_model`|
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

1. `require_paid` field + select gate + explicit `ModelUnavailable` for `require_paid ∧ ¬allow_paid`
   (+ unit tests: require_paid excludes free; the nonsensical combo fails closed with a reason).
2. `RequirementOverrides` typed contract + `route_chat` `overrides=` param + `allow_paid` precedence
   (ValueError on double-supply) + compose/tighten merge with the base profile (+ tests: the
   collision `ValueError`, the synthetic-base-profile union/tighten merge, snapshot-derived default
   when `overrides is None`).
3. Canonical `backends/credits.fresh_paid_headroom_available()` (+ its fail-closed/non-finite tests).
4. `execution_status` ladder → `TierConstraint`/`tier_overrides` + `_paid_escalation_enabled()` exact
   env precedence + legacy deprecation + `paid_tier_usable` delegating to the credits helper +
   `model_tier`/`fix_rounds` bool-safety (+ the tier golden / fabrication / corrupt-state-matrix /
   env-matrix tests; convert the exhaustion-flow model-id assertions to constraint assertions).
5. Walker `overrides` threading (`router.py`) (+ walker→route_chat propagation tests).
6. Speckit + convergence threading (context, agent, reviewspecs, reviewer, reviser) (+ the
   5-hop + concurrent-reviewer propagation tests through the real reviewspec→panel→reviewer path).
7. Graph rewiring (dispatch + escalation logs) (+ the routing tests stay green).
8. Spec delta + manifest regen (+ inventory test update; frozen drift test green).
9. Full non-slow backstop; ruff; `git diff --check`; regenerate the resume handoff note.
