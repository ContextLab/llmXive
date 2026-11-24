# Slice 6 — Execution-Tier Constraints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded execution-tier model-id ladder (`FREE_MODEL_TIERS`) with escalating requirement *constraints* applied through `route_chat`/`select`, so escalation carries no model-id literals.

**Architecture:** A per-project integer `model_tier` (unchanged state machine) now resolves to a frozen `TierConstraint` → a typed immutable `RequirementOverrides`, threaded parallel to the existing `model=` channel (walkers → speckit agent + convergence reviewer/reviser) into `route_chat`, which composes the overrides onto the base profile's requirement (union excludes, tighten `max_credits`, OR `require_paid`, explicit `allow_paid`) and runs the pure `select`. A new `require_paid` cost-class field makes a paid rung genuinely reach the paid model despite free-before-paid ordering.

**Tech Stack:** Python ≥ 3.11, dataclasses (frozen), pytest, ruff. No new deps.

**Design doc:** [2026-07-18-issue-1242-slice6-design.md](2026-07-18-issue-1242-slice6-design.md) (maintainer-approved, round-2 clarifications folded in).

## Global Constraints

- **Commit prefix:** every commit runs `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit …`; verify HEAD moved. Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Branch:** `026-model-selection-consolidation` (do NOT push; rebase onto origin/main only at PR time — local main lags ~655 commits).
- **No model-id literals** may be (re)introduced into `state/execution_status.py`. Model knowledge lives in `model_selection/policy.py` / the catalog.
- **Free-first + fail-closed:** every free/fail-safe rung sets `allow_paid=False` EXPLICITLY. Corrupt/out-of-range tier → tier 0 / free-only, never the last paid rung. Fabrication (`free_only=True`) never reaches an `is_paid` rung.
- **Constitution I:** paid-headroom arithmetic lives ONLY in `backends/credits.py`. **Constitution III:** real calls, no mocks as the primary path (offline suites use the autouse snapshot stub already in `tests/conftest.py`).
- **Leave unrelated worktree noise alone:** `projects/PROJ-317-…/docs/CONTRIBUTING.md` (M), the untracked `notes/2026-07-15-issue-1139-audit-*.md`, and `state/run-log/**` — NOT ours.
- **Test command (targeted):** `.venv/bin/python -m pytest <paths> -q`. **Ruff:** `.venv/bin/ruff check <paths>`.

## File Structure

| file | responsibility (this slice) |
|-|-|
|`src/llmxive/model_selection/types.py`|add `ModelRequirement.require_paid`; add frozen `RequirementOverrides`|
|`src/llmxive/model_selection/select.py`|one-line `require_paid` free-exclusion; explicit no-candidate reason|
|`src/llmxive/model_selection/route.py`|`overrides=` param; `allow_paid` precedence; compose/tighten merge; drop `**requirement_overrides`|
|`src/llmxive/backends/credits.py`|new canonical `fresh_paid_headroom_available()`|
|`src/llmxive/state/execution_status.py`|`TierConstraint`; `tier_overrides`/`tier_constraint`; `model_tier_ladder`→constraints; `paid_tier_usable` delegates; `_paid_escalation_enabled()` + env precedence; `model_tier`/`fix_rounds` bool-safety; remove `FREE_MODEL_TIERS`/`execution_model_override`/`tier_model`|
|`src/llmxive/backends/router.py`|`overrides=` on the 4 walkers → `route_chat`|
|`src/llmxive/speckit/slash_command.py`|`SlashCommandContext.requirement_overrides`; `run()` forwards it|
|`src/llmxive/convergence/reviewspecs.py`|thread overrides through builders/`_wire_live_panel`; set reviser field|
|`src/llmxive/convergence/llm_reviewer.py`|`build_panel`/`LLMReviewer` carry+forward `_overrides`|
|`src/llmxive/convergence/revisers/_self_consistency.py`|`invoke_reviser_backend` reads the reviser's declared `_overrides`|
|`src/llmxive/pipeline/graph.py`|dispatch sets `requirement_overrides`; escalation logs describe the constraint|
|`specs/026-model-selection-consolidation/{spec.md,migration_manifest.*}`|FR-003 + US6/SC-007 delta; regen manifest|

---

### Task 1: `require_paid` requirement field + select gate

**Files:**
- Modify: `src/llmxive/model_selection/types.py:143-168` (add field), `src/llmxive/model_selection/select.py:180-195` (gate + reason)
- Test: `tests/unit/test_model_selection_select.py`

**Interfaces:**
- Produces: `ModelRequirement.require_paid: bool = False`. select() excludes ALL free candidates when `require_paid` is True; when that leaves no admissible paid candidate it raises `ModelUnavailable` with a `require_paid`-specific reason.

- [ ] **Step 1: Write the failing tests** — append to `tests/unit/test_model_selection_select.py`. Reuse the module's existing snapshot builder (grep the file for the fixture/helper that builds a `RuntimeSnapshot` with qwen/gemma/gpt-oss/claude + a live opted-in `CreditGuardSnapshot`; mirror an existing paid-admitting test for the credit setup).

```python
def test_require_paid_excludes_all_free_and_leads_with_paid():
    # allow_paid + require_paid + live/opted-in credit with headroom → only the
    # paid candidate (claude-haiku) survives; free (qwen/gemma/gpt-oss/local) excluded.
    snap = _snapshot_paid_admissible()  # existing helper (live credit, opt-in, headroom)
    req = _req(capability="deep", allow_paid=True, require_paid=True, max_candidates=8)
    chain = select(req, snap)
    ids = [c.model_ref.model_id for c in chain.candidates]
    assert ids and all("claude" in i for i in ids)  # paid-only; no free ids present

def test_require_paid_with_allow_paid_false_fails_closed():
    snap = _snapshot_paid_admissible()
    req = _req(capability="deep", allow_paid=False, require_paid=True)
    with pytest.raises(ModelUnavailable) as exc:
        select(req, snap)
    assert "require_paid" in str(exc.value).lower()

def test_require_paid_over_ceiling_fails_closed():
    # paid admissible in general, but per-call worst_case > cap → paid excluded,
    # free excluded by require_paid → ModelUnavailable (does NOT fall back to free).
    snap = _snapshot_paid_admissible(headroom_credits=0.0001)
    req = _req(capability="deep", allow_paid=True, require_paid=True, max_candidates=8)
    with pytest.raises(ModelUnavailable):
        select(req, snap)
```

- [ ] **Step 2: Run — expect FAIL** (`AttributeError`/`TypeError`: `require_paid` unknown, or the paid-only assertion fails).

Run: `.venv/bin/python -m pytest tests/unit/test_model_selection_select.py -k require_paid -q`
Expected: FAIL.

- [ ] **Step 3: Add the field** in `types.py`, after `max_candidates` (line 161), before `require_fresh_snapshot`:

```python
    #: Cost-class escalation (spec 026 slice 6): when True, EVERY free candidate is
    #: excluded so a paid escalation rung genuinely reaches the paid model despite the
    #: free-before-paid tie-break. Only meaningful with allow_paid=True; the combination
    #: require_paid=True + allow_paid=False admits no candidate and fails closed
    #: (ModelUnavailable) — it is never silently reinterpreted.
    require_paid: bool = False
```

- [ ] **Step 4: Add the gate** in `select.py`. In the per-model loop, section `(f) paid guard` (around line 184, right after `is_free = pricing.is_free`), add:

```python
        if requirement.require_paid and is_free:
            continue  # require_paid rung: exclude every free candidate (spec 026 slice 6)
```

- [ ] **Step 5: Make the no-candidate reason explicit.** In `_no_candidate_reason` (line 248) add `require_paid` to the message so the failing-closed combo is diagnosable:

```python
        f"required_independence={set(requirement.required_independence) or '∅'}, "
        f"require_paid={requirement.require_paid}) "
```
(insert `require_paid=...` into the existing f-string args near `allow_paid=...`).

- [ ] **Step 6: Run — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_model_selection_select.py -q`
Expected: PASS (all, incl. pre-existing).

- [ ] **Step 7: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/model_selection/types.py src/llmxive/model_selection/select.py tests/unit/test_model_selection_select.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): require_paid cost-class field + select free-exclusion gate

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `RequirementOverrides` contract + `route_chat` precedence & compose-merge

**Files:**
- Modify: `src/llmxive/model_selection/types.py` (add `RequirementOverrides`), `src/llmxive/model_selection/route.py:120-199`
- Test: `tests/unit/test_model_selection_route.py`

**Interfaces:**
- Produces: `RequirementOverrides(allow_paid: bool | None = None, require_paid: bool = False, exclude_models: frozenset[str] = frozenset(), max_credits: int | None = None)` (frozen). `route_chat(..., overrides: RequirementOverrides | None = None)` — raises `ValueError` if both the standalone `allow_paid` param and `overrides.allow_paid` are non-None; composes overrides onto the profile's base requirement (union `exclude_models`, tighter `max_credits`, `require_paid = base or override`).
- Consumes: `ModelRequirement.require_paid` (Task 1).

- [ ] **Step 1: Write the failing tests** — append to `tests/unit/test_model_selection_route.py` (reuse its existing snapshot/backend-factory fixtures; grep for how existing route tests inject `snapshot=` and a fake `backend_factory`).

```python
def test_allow_paid_double_supply_raises():
    with pytest.raises(ValueError, match="allow_paid"):
        route_chat([_msg("hi")], max_tokens=64, allow_paid=True,
                   overrides=RequirementOverrides(allow_paid=False),
                   snapshot=_snap_free())

def test_overrides_allow_paid_wins_over_snapshot_optin():
    # snapshot opt-in True, but overrides pins allow_paid=False → no paid candidate.
    captured = {}
    def fake_select(req, snap, **k):
        captured["req"] = req
        return _free_chain()
    monkey_select(fake_select)  # monkeypatch route.select
    route_chat([_msg("hi")], max_tokens=64,
               overrides=RequirementOverrides(allow_paid=False),
               snapshot=_snap_optin_true(), backend_factory=_fake_factory())
    assert captured["req"].allow_paid is False

def test_overrides_compose_union_and_tighten_with_base_profile():
    # base profile carries an existing exclusion + a max_credits; overrides must
    # UNION excludes and take the TIGHTER max_credits, never erase them.
    captured = {}
    monkey_select(lambda req, snap, **k: captured.__setitem__("req", req) or _free_chain())
    monkey_build_requirement_base(exclude_models=frozenset({"vendor.base-x"}), max_credits=500)
    route_chat([_msg("hi")], max_tokens=64,
               overrides=RequirementOverrides(exclude_models=frozenset({"q.default"}),
                                              max_credits=200, require_paid=True),
               snapshot=_snap_free(), backend_factory=_fake_factory())
    req = captured["req"]
    assert req.exclude_models == frozenset({"vendor.base-x", "q.default"})  # union
    assert req.max_credits == 200                                          # tighter
    assert req.require_paid is True                                         # base(False) OR True

def test_overrides_none_preserves_snapshot_derived_allow_paid():
    captured = {}
    monkey_select(lambda req, snap, **k: captured.__setitem__("req", req) or _free_chain())
    route_chat([_msg("hi")], max_tokens=64, overrides=None,
               snapshot=_snap_optin_true(), backend_factory=_fake_factory())
    assert captured["req"].allow_paid is True  # from snapshot opt-in (unchanged behavior)
```
(If the test module lacks `monkey_select`/`monkey_build_requirement_base` helpers, write them inline with `monkeypatch.setattr(llmxive.model_selection.route, "select", …)` and a `RequirementProfile` with the given `exclude_models`/`max_credits` injected via `monkeypatch.setitem(PROFILES, "standard_generation", …)`.)

- [ ] **Step 2: Run — expect FAIL** (`RequirementOverrides`/`overrides=` unknown).

Run: `.venv/bin/python -m pytest tests/unit/test_model_selection_route.py -k "overrides or double_supply" -q`
Expected: FAIL.

- [ ] **Step 3: Add `RequirementOverrides`** to `types.py` (after `ModelRequirement`):

```python
@dataclass(frozen=True)
class RequirementOverrides:
    """Escalation constraints applied ON TOP of a base profile's requirement
    (spec 026 slice 6). Frozen/typed so the large call graph carries an immutable
    value (safe across the panel ThreadPoolExecutor) with a fixed, validated field
    set — never an arbitrary mapping. Merge semantics (in route_chat): allow_paid is
    explicit tier authority; require_paid ORs; exclude_models unions; max_credits
    tightens. ``allow_paid=None`` means 'defer to the standalone param / snapshot'."""

    allow_paid: bool | None = None
    require_paid: bool = False
    exclude_models: frozenset[str] = frozenset()
    max_credits: int | None = None
```

- [ ] **Step 4: Rewrite `route_chat`'s requirement build** (`route.py:120-198`). Change the signature: replace the trailing `**requirement_overrides: object,` with `overrides: RequirementOverrides | None = None,`. Replace the `allow_paid_eff`/`build_requirement` block (lines ~170-184) with:

```python
    snap = snapshot if snapshot is not None else _acquire_snapshot()

    # allow_paid precedence (spec 026 slice 6, round-2 #1): no silent precedence.
    if allow_paid is not None and overrides is not None and overrides.allow_paid is not None:
        raise ValueError(
            "allow_paid supplied both directly and through overrides — pass exactly one"
        )
    if overrides is not None and overrides.allow_paid is not None:
        allow_paid_eff = overrides.allow_paid
    elif allow_paid is not None:
        allow_paid_eff = allow_paid
    else:
        allow_paid_eff = snap.credit.paid_opt_in

    call_budget = call_budget_for(msg_list, max_tokens)
    base = build_requirement(
        profile, call_budget,
        independence_against=independence_against,
        allow_paid=allow_paid_eff,
    )
    if overrides is None:
        requirement = base
    else:
        requirement = replace(
            base,
            require_paid=base.require_paid or overrides.require_paid,
            exclude_models=base.exclude_models | overrides.exclude_models,
            max_credits=_tighter_credits(base.max_credits, overrides.max_credits),
        )
    chain = select(requirement, snap)
```

- [ ] **Step 5: Add the tightening helper** to `route.py` (module level) and the `RequirementOverrides`/`replace` imports (top of file already imports `replace` from dataclasses; add `RequirementOverrides` to the `types` import):

```python
def _tighter_credits(a: int | None, b: int | None) -> int | None:
    """The TIGHTER (smaller) per-call credit ceiling: the set one when only one is
    set, else min(). None means 'no ceiling' — a set ceiling always wins."""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)
```
Update `__all__` to add `RequirementOverrides` if route re-exports it (else export from `types`).

- [ ] **Step 6: Run — expect PASS** (route + select suites).

Run: `.venv/bin/python -m pytest tests/unit/test_model_selection_route.py tests/unit/test_model_selection_select.py -q`
Expected: PASS. If a pre-existing route test passed `foo=bar` via the old `**requirement_overrides`, convert it to `overrides=RequirementOverrides(...)` (there should be none in production callers — only the walkers call route_chat).

- [ ] **Step 7: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/model_selection/types.py src/llmxive/model_selection/route.py tests/unit/test_model_selection_route.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): typed RequirementOverrides + route_chat precedence & compose-merge

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Canonical `fresh_paid_headroom_available()` in `backends/credits.py`

**Files:**
- Modify: `src/llmxive/backends/credits.py` (add function near `paid_call_allowed`, ~line 181)
- Test: `tests/unit/test_credits_guard.py` (or the existing credits test module — grep `tests/` for `paid_call_allowed`/`budget_fraction` and append there)

**Interfaces:**
- Produces: `fresh_paid_headroom_available(*, fetch: Callable[[], CreditBalance] | None = None) -> tuple[bool, str]`. Cache-bypassing, opt-in-gated, non-finite-rejecting, fail-closed, `False` when headroom `<= 0`.

- [ ] **Step 1: Write the failing tests.**

```python
from llmxive.backends import credits

def _bal(spend, max_budget):
    return credits.CreditBalance(account="a", spend=spend, max_budget=max_budget,
                                 budget_duration="1d", budget_reset_at="t")

def test_headroom_opt_in_off_false(monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    ok, reason = credits.fresh_paid_headroom_available(fetch=lambda: _bal(0, 1000))
    assert ok is False and "opt-in" in reason.lower()

def test_headroom_positive_true(monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    monkeypatch.delenv("LLMXIVE_PAID_BUDGET_FRACTION", raising=False)  # default 0.75
    ok, _ = credits.fresh_paid_headroom_available(fetch=lambda: _bal(100, 1000))
    assert ok is True  # cap 750 - spend 100 = 650 > 0

def test_headroom_exhausted_false(monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    ok, reason = credits.fresh_paid_headroom_available(fetch=lambda: _bal(800, 1000))
    assert ok is False  # cap 750 <= spend 800

def test_headroom_nonfinite_fails_closed(monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    ok, _ = credits.fresh_paid_headroom_available(fetch=lambda: _bal(float("nan"), 1000))
    assert ok is False

def test_headroom_fetch_error_fails_closed(monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    def boom(): raise RuntimeError("network")
    ok, reason = credits.fresh_paid_headroom_available(fetch=boom)
    assert ok is False and "failing closed" in reason.lower()
```

- [ ] **Step 2: Run — expect FAIL** (`AttributeError`).

Run: `.venv/bin/python -m pytest tests/unit/test_credits_guard.py -k headroom -q`
Expected: FAIL.

- [ ] **Step 3: Implement** in `credits.py` (add `import math` if absent):

```python
def fresh_paid_headroom_available(
    *, fetch: Callable[[], CreditBalance] | None = None
) -> tuple[bool, str]:
    """Coarse escalation gate (spec 026 slice 6): is paid globally enabled AND is
    there daily headroom RIGHT NOW? Reads a FRESH, cache-bypassing balance (a
    concurrent burst must not slip past a stale spend), applies the canonical
    budget_fraction, and FAILS CLOSED on any doubt. This is the ONLY paid-headroom
    arithmetic outside select()'s per-call ceiling and execute()'s authoritative
    reservation (Constitution I) — the escalation ladder delegates here rather than
    re-deriving the cap. Returns (allowed, reason)."""
    if not paid_opt_in_enabled():
        return (False, f"paid escalation refused: {PAID_OPT_IN_ENV} is not set")
    try:
        balance = (fetch or fetch_credit_balance)()  # cache-bypassing (fresh)
    except Exception as exc:
        return (False, f"paid escalation refused: balance unavailable "
                       f"({type(exc).__name__}: {exc}) — failing closed")
    frac = budget_fraction()
    if not all(math.isfinite(v) for v in (balance.spend, balance.max_budget, frac)):
        return (False, "paid escalation refused: non-finite spend/max_budget/fraction "
                       "— failing closed")
    if balance.max_budget <= 0:
        return (False, f"paid escalation refused: max_budget={balance.max_budget} "
                       "(no paid budget on this account)")
    cap = frac * balance.max_budget
    headroom = cap - balance.spend
    if not (math.isfinite(cap) and math.isfinite(headroom)):
        return (False, "paid escalation refused: non-finite cap/headroom — failing closed")
    if headroom <= 0:
        return (False, f"paid escalation refused: no headroom "
                       f"(cap {cap:.2f} <= spend {balance.spend:.2f})")
    return (True, f"paid escalation allowed: headroom {headroom:.2f} "
                  f"(cap {cap:.2f}, spend {balance.spend:.2f})")
```

- [ ] **Step 4: Run — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_credits_guard.py -k headroom -q`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/backends/credits.py tests/unit/test_credits_guard.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): canonical fresh_paid_headroom_available() (Constitution I)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Rebuild the execution-tier ladder on `TierConstraint`

**Files:**
- Modify: `src/llmxive/state/execution_status.py` (constants + tier functions; remove `FREE_MODEL_TIERS`, `execution_model_override`, `tier_model`, `EXECUTION_PAID_TIERS_ENV`, `_paid_model_tiers`)
- Test: `tests/unit/test_execution_exhaustion_flow.py` (convert), plus new `tests/unit/test_execution_tier_constraints.py`

**Interfaces:**
- Produces:
  - `TierConstraint(allow_paid=False, exclude_registered_default=False, require_paid=False, max_credits=None)` with `.is_paid` property and `.to_overrides(default_model) -> RequirementOverrides`.
  - `model_tier_ladder() -> tuple[TierConstraint, ...]`
  - `tier_constraint(tier: int) -> TierConstraint` (out-of-range/corrupt → tier-0 free-only)
  - `tier_overrides(project_id, *, default_model, repo_root=None) -> RequirementOverrides`
  - `paid_tier_usable() -> bool` (no `model` arg — delegates to `credits.fresh_paid_headroom_available`)
  - `next_usable_tier(current, *, free_only=False) -> int | None` (unchanged shape; now uses `constraint.is_paid`)
  - `PAID_ESCALATION_ENV = "LLMXIVE_EXECUTION_PAID_ESCALATION"`
- Consumes: `RequirementOverrides` (Task 2), `fresh_paid_headroom_available` (Task 3).

- [ ] **Step 1: Write the new constraint tests** — new file `tests/unit/test_execution_tier_constraints.py`:

```python
import math
import pytest
from llmxive.state import execution_status as es
from llmxive.model_selection.types import RequirementOverrides

@pytest.fixture(autouse=True)
def _free_first(monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_ESCALATION", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_TIERS", raising=False)

def test_tier0_is_free_only_even_when_opt_in_true(monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    ov = es.tier_constraint(0).to_overrides("q.default")
    assert ov.allow_paid is False and ov.require_paid is False
    assert ov.exclude_models == frozenset()

def test_tier1_free_second_opinion_excludes_default():
    ov = es.tier_constraint(1).to_overrides("q.default")
    assert ov.allow_paid is False
    assert ov.exclude_models == frozenset({"q.default"})

def test_corrupt_tier_resolves_free_only():
    for bad in (-1, True, 2.5, "1", 10**9):
        c = es.tier_constraint(bad)  # type: ignore[arg-type]
        assert c.allow_paid is False and c.require_paid is False

def test_paid_rung_present_only_when_enabled(monkeypatch):
    assert all(not c.is_paid for c in es.model_tier_ladder())  # free-only default
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ladder = es.model_tier_ladder()
    assert sum(c.is_paid for c in ladder) == 1  # exactly one paid rung
    paid = next(c for c in ladder if c.is_paid)
    assert paid.allow_paid is True and paid.require_paid is True

def test_paid_rung_to_overrides_is_require_paid(monkeypatch):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    ov = es.model_tier_ladder()[-1].to_overrides("q.default")
    assert ov.allow_paid is True and ov.require_paid is True

def test_env_precedence_new_zero_beats_legacy(monkeypatch):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_TIERS", "anthropic.claude-haiku")
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "0")
    assert all(not c.is_paid for c in es.model_tier_ladder())  # explicit off wins

def test_env_legacy_only_enables_one_rung_with_warning(monkeypatch, caplog):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_TIERS", "a.b,c.d,c.d")
    import logging
    with caplog.at_level(logging.WARNING):
        ladder = es.model_tier_ladder()
    assert sum(c.is_paid for c in ladder) == 1
    assert sum("deprecated" in r.message.lower() for r in caplog.records) >= 1

def test_env_invalid_new_value_fails_closed(monkeypatch):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "banana")
    assert all(not c.is_paid for c in es.model_tier_ladder())  # invalid → off

def test_next_usable_tier_skips_paid_when_opt_in_off(monkeypatch):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")  # ladder has paid rung
    # opt-in OFF → paid unusable
    assert es.next_usable_tier(0) == 1               # free second opinion
    assert es.next_usable_tier(1) is None            # paid skipped (opt-in off)

def test_fabrication_free_only_never_reaches_paid(monkeypatch):
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    monkeypatch.setattr(es, "paid_tier_usable", lambda: True)  # opt-in ON, headroom
    assert es.next_usable_tier(1) == 2                       # paid reachable generally
    assert es.next_usable_tier(1, free_only=True) is None    # ...but not free_only
    assert es.next_usable_tier(0, free_only=True) == 1
```

- [ ] **Step 2: Run — expect FAIL** (`AttributeError`: `TierConstraint`/`tier_constraint`/`tier_overrides`).

Run: `.venv/bin/python -m pytest tests/unit/test_execution_tier_constraints.py -q`
Expected: FAIL.

- [ ] **Step 3: Rewrite the ladder region** of `execution_status.py`. Delete `FREE_MODEL_TIERS` (line 63), `EXECUTION_PAID_TIERS_ENV` (66), `_paid_model_tiers` (69-74), `model_tier_ladder` (77-85), `paid_tier_usable` (88-105), `tier_model` (146-152), `execution_model_override` (155-174), `_is_free_tier` (177-180). Replace with:

```python
from llmxive.model_selection.types import RequirementOverrides

#: Env: enable the single PAID escalation rung (default off). Booleans use the
#: canonical {"1","true","yes","on"} idiom (mirrors backends.credits).
PAID_ESCALATION_ENV = "LLMXIVE_EXECUTION_PAID_ESCALATION"
#: Deprecated: a comma-separated model-id list. Model-ids are NO LONGER honored;
#: any nonempty value collapses to ONE paid rung (with a one-time warning). Removal
#: tracked for slice 8.
_LEGACY_PAID_TIERS_ENV = "LLMXIVE_EXECUTION_PAID_TIERS"
_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}
_LEGACY_WARNED = False


@dataclass(frozen=True)
class TierConstraint:
    """One escalation rung as REQUIREMENT overrides — never a model id (spec 026
    slice 6). Resolved to RequirementOverrides at dispatch."""
    allow_paid: bool = False
    exclude_registered_default: bool = False
    require_paid: bool = False
    max_credits: int | None = None

    @property
    def is_paid(self) -> bool:
        return self.allow_paid or self.require_paid

    def to_overrides(self, default_model: str) -> RequirementOverrides:
        return RequirementOverrides(
            allow_paid=self.allow_paid,  # ALWAYS explicit (incl. False)
            require_paid=self.require_paid,
            exclude_models=(
                frozenset({default_model})
                if self.exclude_registered_default and default_model
                else frozenset()
            ),
            max_credits=self.max_credits,
        )


#: The free rungs (indices stable): tier 0 = base free; tier 1 = free second opinion
#: (exclude the registered default so the policy's next-best free leads).
_FREE_RUNGS: tuple[TierConstraint, ...] = (
    TierConstraint(allow_paid=False),
    TierConstraint(allow_paid=False, exclude_registered_default=True),
)
#: The single paid rung appended when paid escalation is enabled.
_PAID_RUNG = TierConstraint(allow_paid=True, require_paid=True)


def _paid_escalation_enabled() -> bool:
    """Exact env precedence (spec 026 slice 6, round-2 #4):
    (a) PAID_ESCALATION present → true=on, false/0=off, invalid=warn+off; legacy ignored.
    (b) else legacy PAID_TIERS nonempty → on (one rung) + one-time deprecation warning.
    (c) else off."""
    global _LEGACY_WARNED
    raw = os.environ.get(PAID_ESCALATION_ENV)
    if raw is not None:
        v = raw.strip().lower()
        if v in _BOOL_TRUE:
            return True
        if v in _BOOL_FALSE or v == "":
            return False
        logger.warning(
            "%s=%r is not a recognized boolean — disabling paid escalation (fail closed)",
            PAID_ESCALATION_ENV, raw,
        )
        return False
    legacy = os.environ.get(_LEGACY_PAID_TIERS_ENV, "").strip()
    if legacy:
        if not _LEGACY_WARNED:
            logger.warning(
                "%s is deprecated; model-ids are no longer honored — collapsing to ONE "
                "paid escalation rung. Use %s=1 instead.",
                _LEGACY_PAID_TIERS_ENV, PAID_ESCALATION_ENV,
            )
            _LEGACY_WARNED = True
        return True
    return False


def model_tier_ladder() -> tuple[TierConstraint, ...]:
    """The ordered escalation ladder as constraints (index = tier). Two free rungs,
    plus ONE paid rung when paid escalation is enabled."""
    return (*_FREE_RUNGS, _PAID_RUNG) if _paid_escalation_enabled() else _FREE_RUNGS


def tier_constraint(tier: int) -> TierConstraint:
    """The constraint for ``tier``. Corrupt/out-of-range (incl. bool/float/str) →
    tier-0 FREE-ONLY (NEVER the last/paid rung — invalid state must not broaden
    spending authority)."""
    ladder = model_tier_ladder()
    t = _nonneg_int(tier)
    if t == 0 or t >= len(ladder):
        return ladder[0]
    return ladder[t]


def paid_tier_usable() -> bool:
    """Coarse gate: is paid escalation globally enabled AND is there fresh daily
    headroom NOW? Delegates ALL arithmetic to the canonical credits helper
    (Constitution I). Fails closed on any error."""
    try:
        from llmxive.backends.credits import fresh_paid_headroom_available
        ok, _reason = fresh_paid_headroom_available()
        return bool(ok)
    except Exception as exc:  # never let the guard crash routing
        logger.warning("paid_tier_usable check failed: %s", exc)
        return False


def tier_overrides(
    project_id: str, *, default_model: str, repo_root: Path | None = None
) -> RequirementOverrides:
    """The RequirementOverrides for the project's CURRENT model tier."""
    return tier_constraint(model_tier(project_id, repo_root=repo_root)).to_overrides(default_model)
```

- [ ] **Step 4: Fix `next_usable_tier`** (was lines 183-206) to use `constraint.is_paid`:

```python
def next_usable_tier(current: int, *, free_only: bool = False) -> int | None:
    """The next tier ABOVE ``current`` whose rung is usable, or None. A paid rung
    (constraint.is_paid) is skipped when ``free_only`` OR paid is not usable now."""
    ladder = model_tier_ladder()
    for t in range(_nonneg_int(current) + 1, len(ladder)):
        c = ladder[t]
        if not c.is_paid:
            return t
        if free_only:
            continue
        if paid_tier_usable():
            return t
    return None
```

- [ ] **Step 5: Bool-safety fix** — route `model_tier` (line 143) and `fix_rounds` (line 136) through `_nonneg_int` (already bool-safe, excludes `bool`):

```python
def fix_rounds(project_id: str, *, repo_root: Path | None = None) -> int:
    rec = load(project_id, repo_root=repo_root) or {}
    return _nonneg_int(rec.get("fix_rounds"))

def model_tier(project_id: str, *, repo_root: Path | None = None) -> int:
    """Current execution-fix-loop model tier (default 0 = registered default)."""
    rec = load(project_id, repo_root=repo_root) or {}
    return _nonneg_int(rec.get("model_tier"))
```
(`_nonneg_int` is defined later at line 308; move it ABOVE these two — or since it's module-level, Python resolves it at call time, so no move needed. Keep as-is; the functions reference it at call time.) Update `__all__`: remove `EXECUTION_PAID_TIERS_ENV`, `FREE_MODEL_TIERS`, `execution_model_override`, `tier_model`; add `PAID_ESCALATION_ENV`, `TierConstraint`, `tier_constraint`, `tier_overrides`.

- [ ] **Step 6: Run the new tests — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_execution_tier_constraints.py -q`
Expected: PASS.

- [ ] **Step 7: Convert `test_execution_exhaustion_flow.py`** — its model-id assertions must become constraint assertions; the ROUTING outcomes stay identical.
  - `test_ladder_skips_paid_tiers_when_opt_in_off`: replace the `model_tier_ladder() == ("", "openai.gpt-oss-120b", ...)` and `LLMXIVE_EXECUTION_PAID_TIERS=...` setup with `LLMXIVE_EXECUTION_PAID_ESCALATION=1`; assert `len(model_tier_ladder()) == 3`, `next_usable_tier(0) == 1`, `next_usable_tier(1) is None` (opt-in off). Keep the `bump_model_tier` 0→1 then raise-at-1 assertions.
  - `test_fabrication_escalation_never_climbs_to_a_paid_tier`: swap the paid-tiers env for `PAID_ESCALATION=1`; `monkeypatch.setattr(es, "paid_tier_usable", lambda: True)` (drop the `m` arg). Keep the `free_only` raise assertions.
  - `test_execution_model_override_resolves_tier` → rewrite as `tier_overrides`: tier 0 → `RequirementOverrides(allow_paid=False, ...)` with empty excludes; after `bump_model_tier`, tier 1 → `exclude_models == {"REGISTERED-DEFAULT"}`, `allow_paid False`.
  - `test_model_tier_defaults_to_zero_and_record_preserves_it`, the graph routing tests (`test_at_cap_*`, `test_below_cap_*`, re-plan/`human_input_needed` recovery): UNCHANGED (they assert tiers/rounds/stages, not model-ids).

- [ ] **Step 8: Run the converted flow + kickback tests — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_execution_exhaustion_flow.py tests/unit/test_execution_replan_cap.py tests/unit/test_convergence_kickback_flow.py -q`
Expected: PASS.

- [ ] **Step 9: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/state/execution_status.py tests/unit/test_execution_tier_constraints.py tests/unit/test_execution_exhaustion_flow.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): execution-tier ladder on TierConstraint (no model-id literals)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Thread `overrides` through the router walkers

**Files:**
- Modify: `src/llmxive/backends/router.py:268-360` (`_walker_route`, `chat_with_model_fallback`, `reasoning_chat`, `chat_with_fallback`)
- Test: `tests/unit/test_chat_with_fallback_delegation.py` (+ the reasoning/reviewer walker delegation tests)

**Interfaces:**
- Produces: each walker gains `overrides: RequirementOverrides | None = None`, forwarded to `route_chat(overrides=...)`. Default `None` → existing callers unaffected.
- Consumes: `route_chat(overrides=...)` (Task 2).

- [ ] **Step 1: Write the failing test** — assert the override reaches `route_chat`:

```python
def test_reasoning_chat_forwards_overrides(monkeypatch):
    import llmxive.backends.router as router
    from llmxive.model_selection.types import RequirementOverrides
    captured = {}
    def fake_route_chat(messages, **kw):
        captured.update(kw)
        return _fake_response()
    monkeypatch.setattr("llmxive.model_selection.route.route_chat", fake_route_chat)
    ov = RequirementOverrides(allow_paid=False, exclude_models=frozenset({"m"}))
    router.reasoning_chat(_fake_backend(), [_msg("hi")], overrides=ov)
    assert captured["overrides"] is ov
```

- [ ] **Step 2: Run — expect FAIL** (`unexpected keyword 'overrides'`).

Run: `.venv/bin/python -m pytest tests/unit/test_chat_with_fallback_delegation.py -k overrides -q`
Expected: FAIL.

- [ ] **Step 3: Add the param** to all four walkers. `_walker_route` gains `overrides: RequirementOverrides | None = None` (keyword-only) and forwards it in its `route_chat(...)` call (`overrides=overrides`); `chat_with_model_fallback`, `reasoning_chat`, `chat_with_fallback` each gain the same kw param and pass `overrides=overrides` to `_walker_route`/`route_chat`. Import `RequirementOverrides` from `llmxive.model_selection.types` (function-local or top — match the file's existing import style; note route_chat is imported function-locally inside `_walker_route`).

- [ ] **Step 4: Run — expect PASS**, plus the full walker suite (no regressions since default is None).

Run: `.venv/bin/python -m pytest tests/unit/test_chat_with_fallback_delegation.py tests/unit/test_reasoning_walker_delegation.py -q`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/backends/router.py tests/unit/test_chat_with_fallback_delegation.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): thread RequirementOverrides through the router walkers

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Thread `requirement_overrides` through speckit + convergence

**Files:**
- Modify: `src/llmxive/speckit/slash_command.py` (context + `run()`); `src/llmxive/convergence/llm_reviewer.py` (`LLMReviewer.__init__` store, `build_panel` param, `_call_backend`×2 calls); `src/llmxive/convergence/reviewspecs.py` (the 10 `build_*_reviewspec` + `_wire_live_panel` + reviser field-set); `src/llmxive/convergence/revisers/_self_consistency.py` (`invoke_reviser_backend`); the reviser base class/dataclass that needs the declared `_overrides` field; the 7 command call sites (`clarify_cmd`, `paper_clarify_cmd`, `plan_cmd`, `paper_plan_cmd`, `paper_implement_cmd`, `paper_tasks_cmd`, `_tasker_engine_bridge`).
- Test: new `tests/unit/test_slice6_override_propagation.py`

**Interfaces:**
- Consumes: `RequirementOverrides`, the walkers' `overrides=` (Task 5).
- Produces: `SlashCommandContext.requirement_overrides: RequirementOverrides | None = None`; `LLMReviewer(..., overrides=None)` stored as `self._overrides`; reviser objects carry a declared `_overrides` field; `build_*_reviewspec(..., requirement_overrides=None)`.

- [ ] **Step 1: Write the propagation tests** (the concurrent one uses the REAL reviewspec→panel→reviewer path, not `build_panel` in isolation):

```python
def test_slashcommand_run_forwards_overrides(monkeypatch):
    # ctx.requirement_overrides reaches chat_with_fallback(overrides=...)
    captured = {}
    monkeypatch.setattr("llmxive.speckit.slash_command.chat_with_fallback",
                        lambda messages, **kw: (captured.update(kw), _fake_response())[1])
    ov = RequirementOverrides(allow_paid=False)
    ctx = _min_ctx(requirement_overrides=ov)
    _RunnableSlashAgent().run(ctx)  # a minimal concrete agent
    assert captured["overrides"] is ov

def test_reviewer_carries_overrides_and_forwards(monkeypatch):
    captured = {}
    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback",
                        lambda backend, messages, **kw: (captured.update(kw), _fake_response())[1])
    r = LLMReviewer(stage="clarified", lens="scope", backend=_fake_backend(),
                    repo_root=Path("."), model=None, overrides=RequirementOverrides(require_paid=True))
    r.review(_min_review_input())     # drives _call_backend
    assert captured["overrides"].require_paid is True

def test_concurrent_reviewers_share_immutable_override_via_real_path(monkeypatch):
    seen = []
    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback",
                        lambda backend, messages, **kw: (seen.append(kw.get("overrides")), _fake_response())[1])
    ov = RequirementOverrides(allow_paid=True, require_paid=True)
    spec = build_plan_reviewspec(backend=_fake_backend(), repo_root=Path("."),
                                 project_id="P", model=None, requirement_overrides=ov)
    _run_panel_concurrently(spec.reviewers, _min_review_input())  # engine.run_panel-style
    assert seen and all(o is ov for o in seen)  # every reviewer got the SAME immutable value

def test_reviser_declared_overrides_field_reaches_reasoning_chat(monkeypatch):
    captured = {}
    monkeypatch.setattr("llmxive.convergence.revisers._self_consistency.reasoning_chat",
                        lambda backend, messages, **kw: (captured.update(kw), _fake_text())[1])
    spec = build_plan_reviewspec(backend=_fake_backend(), repo_root=Path("."),
                                 project_id="P", model=None,
                                 requirement_overrides=RequirementOverrides(allow_paid=True))
    invoke_reviser_backend(spec.reviser, [_msg("x")])
    assert captured["overrides"].allow_paid is True
```

- [ ] **Step 2: Run — expect FAIL.**

Run: `.venv/bin/python -m pytest tests/unit/test_slice6_override_propagation.py -q`
Expected: FAIL.

- [ ] **Step 3: `SlashCommandContext`** — add the field (`slash_command.py:43-56`):

```python
    requirement_overrides: "RequirementOverrides | None" = None
```
(add to the end of the dataclass; import `RequirementOverrides` from `llmxive.model_selection.types`. Since the dataclass has no defaults before it, adding a defaulted field at the END is safe.) In `run()` (line 117) add `overrides=ctx.requirement_overrides` to the `chat_with_fallback(...)` call.

- [ ] **Step 4: `LLMReviewer`** — `__init__` (line 818) gains `overrides: RequirementOverrides | None = None`; store `self._overrides = overrides` (next to `self._model`, line 845). Both `_call_backend` sites (893, 1100) that call `chat_with_model_fallback(self._backend, ..., model=self._model)` add `overrides=self._overrides`. `build_panel` (line 1110) gains `overrides: RequirementOverrides | None = None` and passes it to each `LLMReviewer(...)`.

- [ ] **Step 5: Reviser declared field.** Find the reviser base/shared construction used by `build_*_reviewspec` (grep `reviewspecs.py` for how it builds the live reviser — the `_TodoReviser` placeholder is swapped for a live reviser). Add a declared `_overrides: RequirementOverrides | None = None` attribute on that reviser class (constructor param or dataclass field — NOT a dynamic setattr). `invoke_reviser_backend` (`_self_consistency.py:147-168`) reads `getattr(reviser, "_overrides", None)` and passes `overrides=` to `reasoning_chat` (line 167). (`getattr` default keeps back-compat for placeholder revisers that lack the field.)

- [ ] **Step 6: `_wire_live_panel` + builders.** `_wire_live_panel` (`reviewspecs.py:86`) gains `requirement_overrides: RequirementOverrides | None = None`, passes it to `build_panel(overrides=...)` AND sets it on the live reviser it constructs. Each of the 10 `build_*_reviewspec` functions gains `requirement_overrides: RequirementOverrides | None = None` and forwards it to `_wire_live_panel(..., requirement_overrides=requirement_overrides)`.

- [ ] **Step 7: The 7 command call sites** — each `build_*_reviewspec(...)` call in the speckit commands adds `requirement_overrides=ctx.requirement_overrides`. (Grep each: `clarify_cmd.py:255`, `paper_clarify_cmd.py:229`, `paper_plan_cmd.py:152`, `paper_implement_cmd.py:295`, `_tasker_engine_bridge.py:292`, `plan_cmd.py:465`, `paper_tasks_cmd.py:170`.)

- [ ] **Step 8: Run — expect PASS**, plus the convergence suites to prove no regression (default None everywhere).

Run: `.venv/bin/python -m pytest tests/unit/test_slice6_override_propagation.py tests/unit/test_llm_reviewer_model_fallback.py tests/unit/test_reviser_self_consistency.py tests/integration/test_spec_reviser.py -q`
Expected: PASS.

- [ ] **Step 9: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/speckit/ src/llmxive/convergence/ tests/unit/test_slice6_override_propagation.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): thread requirement_overrides through speckit + convergence panel

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Graph rewiring — dispatch sets overrides, escalation logs describe the constraint

**Files:**
- Modify: `src/llmxive/pipeline/graph.py` (~757-800 dispatch; ~1534 and ~1785 escalation logs)
- Test: `tests/unit/test_execution_exhaustion_flow.py` (routing tests stay green); new assertion in `tests/unit/test_slice6_override_propagation.py` for dispatch wiring if practical.

**Interfaces:**
- Consumes: `execution_status.tier_overrides` (Task 4), `SlashCommandContext.requirement_overrides` (Task 6).

- [ ] **Step 1: Rewrite the dispatch block** (`graph.py:770-788`). Replace `_model_for_run = execution_status.execution_model_override(...)` with: set `default_model=entry.default_model` (always the registry default) and compute the escalation overrides:

```python
        _model_for_run = entry.default_model  # registry default (Slice 7 owns per-agent profiles)
        _req_overrides = None
        _exec_fix = agent_name == "implementer" and project.current_stage == Stage.IN_PROGRESS
        _panel_stage = project.current_stage in _STAGE_PANEL_LABEL
        if _exec_fix or _panel_stage:
            _req_overrides = execution_status.tier_overrides(
                project.id, default_model=entry.default_model, repo_root=repo,
            )
            _tier = execution_status.model_tier(project.id, repo_root=repo)
            if _tier > 0:
                logger.info(
                    "model-tier escalation: dispatching %s for %s (stage=%s) at tier %d "
                    "with overrides %r",
                    agent_name, project.id, project.current_stage.value, _tier, _req_overrides,
                )
```
Then set `requirement_overrides=_req_overrides` on the `SlashCommandContext(...)` construction (line 790-803), keeping `default_model=_model_for_run`.

- [ ] **Step 2: Fix the two escalation log lines** (`graph.py:1542` and `1792`) that call `execution_status.tier_model(new_tier)` — replace with a stable constraint description:

```python
                    execution_status.tier_constraint(new_tier),
```
(the `TierConstraint` repr is a stable description; drop the `or "<registered default>"` fallback since a constraint always renders.)

- [ ] **Step 3: Run the routing + propagation tests — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_execution_exhaustion_flow.py tests/unit/test_convergence_kickback_flow.py tests/unit/test_slice6_override_propagation.py -q`
Expected: PASS.

- [ ] **Step 4: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/pipeline/graph.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-6): graph dispatch threads tier overrides; escalation logs describe the constraint

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Spec delta + manifest regeneration

**Files:**
- Modify: `specs/026-model-selection-consolidation/spec.md` (FR-003 + US6/SC-007 delta), `migration_manifest.json` + `.md` (regen), `tests/unit/test_model_selection_inventory.py:323`

**Interfaces:** none (docs + generated artifact).

- [ ] **Step 1: Spec edits.** In `spec.md`: (a) add `require_paid: bool` to the FR-003 `ModelRequirement` field list + the "ModelRequirement" component description ("cost-class: require a paid model, excluding all free"); (b) under US6/SC-007, add a **sanctioned migration delta** paragraph: the tier-1 free second opinion is now the policy-selected next-best free (gemma-4) not the pinned `openai.gpt-oss-120b`; the golden updates from gpt-oss to gemma-4; paid escalation uses `require_paid` and is configured via `LLMXIVE_EXECUTION_PAID_ESCALATION` (legacy `LLMXIVE_EXECUTION_PAID_TIERS` deprecated).

- [ ] **Step 2: Regenerate the manifest.**

Run: `.venv/bin/python -m llmxive.model_selection.inventory`
Expected: writes `migration_manifest.json` + `.md`; the `FREE_MODEL_TIERS` slice-6 row is GONE; no new model-id pin rows appear.

- [ ] **Step 3: Update the inventory test.** `tests/unit/test_model_selection_inventory.py:323` currently asserts the `execution_status.py … FREE_MODEL_TIERS` entry EXISTS — change it to assert that entry is ABSENT (and that no new `state/execution_status.py` model-id pin was introduced).

- [ ] **Step 4: Run the inventory (frozen drift) test — expect PASS.**

Run: `.venv/bin/python -m pytest tests/unit/test_model_selection_inventory.py -q`
Expected: PASS (live scan matches the regenerated manifest).

- [ ] **Step 5: Commit.**

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add specs/026-model-selection-consolidation/ tests/unit/test_model_selection_inventory.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "docs(026 Slice-6): FR-003 require_paid + US6/SC-007 migration delta; regen manifest

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Full backstop + resume note

**Files:** none (verification); update `notes/2026-07-18-issue-1242-slice6-*` handoff.

- [ ] **Step 1: Ruff** on all session-changed src + test files.

Run: `.venv/bin/ruff check src/llmxive/model_selection/ src/llmxive/state/execution_status.py src/llmxive/backends/router.py src/llmxive/backends/credits.py src/llmxive/speckit/ src/llmxive/convergence/ src/llmxive/pipeline/graph.py`
Expected: clean (or pre-existing-only, matching the base commit).

- [ ] **Step 2: `git diff --check`** (whitespace/conflict markers). Expected: no output.

- [ ] **Step 3: Full non-slow backstop.**

Run: `.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q`
Expected: PASS except the 2 PRE-EXISTING `web_data` dashboard-drift failures (`test_web_data_blocks` / `test_web_data_contributors`) noted in the Slice-5 handoff. If ANY other test fails, fix the CODE (never weaken the test) and re-run the FULL backstop.

- [ ] **Step 4: Real-call verification (when `DARTMOUTH_CHAT_API_KEY` is available).** With paid opt-in ON and `LLMXIVE_EXECUTION_PAID_ESCALATION=1`, confirm a tier-2 requirement routes to a paid candidate; with opt-in OFF, `paid_tier_usable()` is False and `next_usable_tier(1)` is None. (SC-008-style; skipped offline.)

- [ ] **Step 5: Regenerate the resume handoff note** (`notes/2026-07-18-issue-1242-slice6-handoff.md`): commit stack, the 2 known pre-existing failures, "rebase onto origin/main before PR", and RESUME-AT for any remaining acceptance (real-call SC-008). Commit it.

---

## Self-Review

**Spec coverage** (design doc §"Required tests" + change map): require_paid (T1) ✓ · RequirementOverrides + precedence + compose-merge (T2) ✓ · canonical headroom helper (T3) ✓ · TierConstraint ladder + env precedence + corrupt-tier + bool-safety + fabrication guard (T4) ✓ · walker threading (T5) ✓ · speckit/convergence 5-hop + concurrent-reviewer + reviser-declared-field (T6) ✓ · graph rewiring (T7) ✓ · spec delta + manifest regen + inventory test (T8) ✓ · backstop + real-call (T9) ✓. Explicit tier golden (tier 0/1/2) is covered by T4 constraint tests + T1 select tests; the end-to-end fixed-snapshot golden (`gemma-4` leads tier 1; `claude` leads tier 2) should be added as a route-or-select test in T2/T4 using the composite snapshot fixture.

**Placeholder scan:** the reviser base class in T6 Step 5 is described by its role + grep pointer (not a line number) because the concrete reviser class name must be confirmed at implementation time — flagged explicitly, not a silent TODO. All code steps carry real code.

**Type consistency:** `RequirementOverrides` fields (`allow_paid: bool|None`, `require_paid: bool`, `exclude_models: frozenset[str]`, `max_credits: int|None`) are identical across T2/T4/T5/T6. `tier_overrides`/`tier_constraint`/`paid_tier_usable()` (no-arg) signatures match between T4 and T7. `overrides=` is the param name on walkers (T5); `requirement_overrides=` on `SlashCommandContext`/builders (T6) — deliberately distinct (the context/builder field vs the route-layer param); the mapping is `chat_with_fallback(overrides=ctx.requirement_overrides)`.

## Execution Handoff

Add one end-to-end golden test (fixed composite snapshot) asserting tier 1 → `gemma-4` leads and tier 2 → `claude` (paid-only) during Task 4, so the sanctioned migration delta is pinned by a test, not just prose.
