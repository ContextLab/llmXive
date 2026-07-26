# Self-Improvement Lane — Slice 1B: Proposal Convergence Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the proposal review onto the Slice-1A substrate — a **lane route context** that carries the mandatory `route_audit` sink AND the `reservation_authority` into every lane LLM call (reviewers *and* the reviser), the FR-002 **two-attempt independence reroute** with an **explicit** `ReviewRerouted` event, the complete `InvocationIdentity`, the `self_improvement_proposal` `ReviewSpec` + lens prompts, and a real `run_convergence` integration test.

**Architecture:** Convergence reviewers already reach `route_chat` (via `chat_with_model_fallback` → `_walker_route`), but that wrapper drops the five spec-025 params. Task 3 closes that gap once, in `_walker_route` + `chat_with_model_fallback`. Everything lane-specific is then new code: `LaneRouteContext` (hooks + route-id minting + the stage LLM-call ceiling), a reroute-aware `LLMReviewer` path, a lane reviser, and a lane entry point that owns fail-closed handling. `run_convergence` itself is **unchanged** — the lane builds independence-aware reviewers *before* handing them to the existing engine.

**Tech Stack:** Python ≥ 3.11; `pytest`; packages `llmxive.self_improvement`, `llmxive.convergence`, `llmxive.backends.router`. No new third-party deps.

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from spec 025 rev 15 and the slice-0/1A contracts.

- **Mandatory audit — no silently-unaudited lane call (FR-033a, F3).** `build_proposal_review_spec` REQUIRES a `LaneRouteContext`; there is no `route_audit=None` default anywhere on the lane path. The context reaches **both** the reviewers and the reviser. A `route_audit` exception is never swallowed: a pre-dispatch failure is route-fatal.
- **Attempt budget on every lane call (FR-033, F2).** `reservation_authority` is threaded through the SAME path as `route_audit` — reviewers and reviser alike. It is consulted by `execute` only for paid candidates (free candidates reserve 0, so the mechanism is inert under the default free-first path), but it MUST be injected on every lane call so a paid candidate can never dispatch outside the Attempt cap.
- **Two-attempt reroute, no new profile (FR-002, ReviewSpec table lines 279-280).** Attempt 1: the delivered **`independent_review`** profile (`required_independence={family}`, `require_fresh_snapshot=True`, `max_catalog_age_s=900`) + `independence_against(<proposer baseline>)`. On **`ModelUnavailable`** → attempt 2: the delivered **`deep_review`** profile (no family constraint, `max_catalog_age_s=3600`) — **degrade, never fail closed** (a proposal produces/merges no code). Only a raw `ModelUnavailable` triggers the reroute: `ChainExhausted`, `RouteAuditError`, and `RouteReplayError` MUST NOT.
- **The degradation record is an EXPLICIT event, never an inference (F10).** A `ReviewRerouted` lane event names `{operation_id, lens, primary_profile, fallback_profile, primary_route_id, fallback_route_id, primary_failure {exception_type, message}, relaxed_constraints}`. `relaxed_constraints = ["family_independence", "snapshot_freshness"]` is FACTUAL (what the fallback always relaxes), NOT a causal claim — `ModelUnavailable` carries only a textual reason and four documented causes, so the code cannot infer WHICH constraint failed.
- **Stage-specific LLM-call ceiling (Policy Contract line 313).** The proposal review is NOT single-route: every reviewer operation is up to two logical `route_chat` invocations, so the proposal ceiling is **`4N + R·(2N + 2)`** (N = panel size, R = `max_rounds`); with N=5, R=3 that is **56**. The `2N` term is R1 (each reviewer: normal call + at most one action-item resubmit), doubled by the reroute; the `+2` is the reviser's at-most-two attempts per round (the engine's malformed-reply retry) and is NOT doubled (the producer has no independence constraint, hence no reroute). **A logical `route_chat` invocation is the unit** — 026's provider-level transient retries are internal and do NOT count. Exceeding the ceiling fails the Attempt.
- **The lane reviser makes EXACTLY ONE `route_chat` call per `revise()`.** The existing `convergence/revisers/*` classes route through `invoke_reviser_backend` → `run_with_self_consistency`, which makes up to THREE calls per `revise()` (first pass + self-consistency audit + corrective re-pass, `_self_consistency.py:147-236`). That would break the `+2`-per-round ceiling term above, so the lane reviser MUST NOT use that path.
- **Convergence types cannot carry the degradation.** `Concern` and `Verdict` are pydantic `_Strict` models (`model_config = ConfigDict(extra="forbid")`, `types.py:128-129`), so no field may be added to them. Provenance lives in lane events (above) — this is why `InvocationIdentity` is sourced from the audit stream, not from `ConvergenceResult`.
- **`run_convergence` is UNCHANGED.** No new parameter, no new branch. Independence is wired into the `Reviewer` objects at construction, before `spec.reviewers` is handed to the engine (spec line 283: "a **025 slice-1 task entirely in `convergence/`**").
- **Behavior-preserving for every existing caller.** With the new params omitted, `chat_with_model_fallback`/`_walker_route`/`LLMReviewer` behave byte-for-byte as today; the research/paper pipeline is untouched. The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`) MUST stay green after every task.
- **Route through the chokepoint; no model-id literals in lane code (SC-008, FR-001).** Reviewers express intent purely via `profile`; `model_selection/enforcement.py` statically verifies no pin is introduced.
- **Real tests, no mocks (Constitution III).** Protocol test doubles with real logic, real temp-git repos, the real `EventStoreRouteAudit`/`AttemptCreditLedger`, and the REAL `run_convergence` engine. `unittest.mock` is not the primary path.
- **Commit discipline.** `PRE_COMMIT_ALLOW_NO_CONFIG=1` + trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved. **Do NOT push.**

## Dependencies + scope boundary

**Consumes (Slice 1A, must be implemented first):** `EventStoreRouteAudit(*, repo, problem_id, attempt_id, actor, clock, config=LaneLogConfig())` (implements slice-0 `RouteAudit`), `AttemptCreditLedger(*, repo, problem_id, attempt_id, attempt_budget_credits, actor, clock, config=LaneLogConfig())` (implements slice-0 `ReservationAuthority`), `LaneLogConfig`, `lane_log.append/read`, `Event`, `derive_event_id`, `KNOWN_EVENT_TYPES_V1`.

**Out of scope (later slices):** the **patch** review (`self_improvement_patch` — fail-closed single-attempt independence; it reuses the `LLMReviewer` mechanism built here but is the pre-merge gate, US3+); the Attempt lifecycle transitions (`proposal_verified`/`rejected` state writes — Slice 1A deliberately deferred Attempt-failure semantics); discovery logic (error mining, issue ranking, the proposer that CREATES a proposal). This plan wires the REVIEW of a proposal, not its creation.

**Deliberately NOT changed:** `reasoning_chat` (`router.py:320-349`) and `invoke_reviser_backend` (`_self_consistency.py:147-179`) keep their current unplumbed behavior. They serve the research/paper pipeline, whose calls are NOT lane calls — the mandatory-sink requirement is scoped to lane LLM calls (SC-008). The lane reviser reaches `route_chat` through the plumbed `chat_with_model_fallback` instead.

## File Structure

- `src/llmxive/self_improvement/route_context.py` — `LaneRouteContext` (the mandatory hooks + route-id minting + ceiling counter) and `LaneCallCeilingExceeded`. One responsibility: what every lane LLM call needs.
- `src/llmxive/self_improvement/events.py` — **modified**: add `ReviewRerouted` to `KNOWN_EVENT_TYPES_V1` (a vocabulary extension — no `SCHEMA_VERSION` bump, per Slice 1A's F7 rule).
- `src/llmxive/self_improvement/invocation_identity.py` — `InvocationIdentity`, `IndependenceDegraded`, `build_invocation_identity`. One responsibility: the audit-derived provenance record.
- `src/llmxive/convergence/lane_reviser.py` — `LaneProposalReviser` (implements `Reviser`; exactly one routed call per `revise()`).
- `src/llmxive/convergence/self_improvement_specs.py` — `PROPOSAL_STAGE`, `PROPOSAL_LENSES`, `build_proposal_review_spec`, `run_proposal_review`.
- `src/llmxive/backends/router.py` — **modified**: `_walker_route` + `chat_with_model_fallback` forward the five spec-025 params.
- `src/llmxive/convergence/llm_reviewer.py` — **modified**: `LLMReviewer.__init__` accepts the lane context + independence params; `_route_review` implements the two-attempt reroute; `_STAGE_PREFIX` gains the lane stage.
- `agents/prompts/panels/panel_si_proposal_<lens>.md` × 5 — the proposal lens prompts.

---

### Task 1: `ReviewRerouted` event type

**Files:**
- Modify: `src/llmxive/self_improvement/events.py`
- Test: `tests/unit/test_self_improvement_events.py` (extend)

**Interfaces:**
- Consumes: `KNOWN_EVENT_TYPES_V1`, `SCHEMA_VERSION`, `SUPPORTED_SCHEMA_VERSIONS` (Slice 1A Task 2).
- Produces: `"ReviewRerouted"` added to `KNOWN_EVENT_TYPES_V1`. **No `SCHEMA_VERSION` bump** — per Slice 1A's F7 rule, extending the event VOCABULARY does not change the record SHAPE, and bumping would make a reader reject prior-version history. The payload contract (documented in the module docstring beside the constant): `{operation_id: str, lens: str, primary_profile: str, fallback_profile: str, primary_route_id: str, fallback_route_id: str, primary_failure: {exception_type: str, message: str}, relaxed_constraints: list[str]}`.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/test_self_improvement_events.py
def test_review_rerouted_is_a_known_event_type():
    # Slice 1B: the explicit FR-002 degradation record (F10) — a VOCABULARY extension,
    # so SCHEMA_VERSION must NOT change (Slice 1A F7: a bump would invalidate history).
    from llmxive.self_improvement.events import KNOWN_EVENT_TYPES_V1, SCHEMA_VERSION
    assert "ReviewRerouted" in KNOWN_EVENT_TYPES_V1
    assert SCHEMA_VERSION == 1

def test_review_rerouted_event_validates():
    from llmxive.self_improvement.events import validate_lane_event
    validate_lane_event(_raw(
        event_type="ReviewRerouted",
        payload={
            "operation_id": "op-1", "lens": "worthwhile-improvement",
            "primary_profile": "independent_review", "fallback_profile": "deep_review",
            "primary_route_id": "r1", "fallback_route_id": "r2",
            "primary_failure": {"exception_type": "ModelUnavailable", "message": "no independent family live"},
            "relaxed_constraints": ["family_independence", "snapshot_freshness"],
        },
    ))  # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_events.py -k review_rerouted -q`
Expected: FAIL — `AssertionError` (`"ReviewRerouted" not in KNOWN_EVENT_TYPES_V1`).

- [ ] **Step 3: Write minimal implementation**

In `src/llmxive/self_improvement/events.py`, add the type to the existing frozenset and document its payload:

```python
KNOWN_EVENT_TYPES_V1 = frozenset({
    "ClaimAcquired", "ClaimReleased", "MonitorStarted", "PromotionEnabledSet",
    "AttemptCreditReserved", "AttemptCreditReleased", "AttemptCreditRetained", "AttemptCreditReconciled",
    "ChainResolved", "SelectionFailure", "ReservationOpened", "DispatchStarted",
    "DispatchCompleted", "DispatchUnknown", "CandidateOutcome",
    "ProblemDiscovered", "Proposed", "ProposalVerified", "Rejected",
    # Slice 1B (FR-002): the EXPLICIT proposal-review degradation record. Payload:
    #   {operation_id, lens, primary_profile, fallback_profile, primary_route_id,
    #    fallback_route_id, primary_failure {exception_type, message},
    #    relaxed_constraints}
    # `relaxed_constraints` is FACTUAL (what the fallback always relaxes), NOT a causal
    # claim about which constraint made the primary fail. A vocabulary extension only —
    # the record SHAPE is unchanged, so SCHEMA_VERSION stays 1 (F7).
    "ReviewRerouted",
})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_events.py -q`
Expected: PASS (all, including the two new tests).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/events.py tests/unit/test_self_improvement_events.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T1): ReviewRerouted event type (vocabulary extension, no schema bump)"
```

---

### Task 2: `LaneRouteContext` — mandatory hooks + route-id minting + call ceiling

**Files:**
- Create: `src/llmxive/self_improvement/route_context.py`
- Test: `tests/unit/test_self_improvement_route_context.py`

**Interfaces:**
- Consumes: slice-0 `RouteAudit`/`ReservationAuthority` protocols; Slice-1A `LaneLogConfig`, `lane_log.append`, `Event`, `derive_event_id`.
- Produces:
  - `class LaneCallCeilingExceeded(RuntimeError)` — the stage's logical-`route_chat` budget is exhausted; the Attempt fails closed (never a silent extra call).
  - `def proposal_call_ceiling(panel_size: int, max_rounds: int) -> int` — `4 * panel_size + max_rounds * (2 * panel_size + 2)` (Policy Contract line 313). Pure function, unit-tested against the spec's arithmetic.
  - `@dataclass class LaneRouteContext`: fields `repo: Path`, `problem_id: str`, `attempt_id: str`, `actor: str`, `clock: Callable[[], str]`, `route_audit: RouteAudit`, `reservation_authority: ReservationAuthority`, `call_ceiling: int`, `config: LaneLogConfig = LaneLogConfig()`. **`route_audit` and `reservation_authority` are REQUIRED** (no `None` default — F2/F3: there is no unaudited or unbudgeted lane call). Not frozen (it carries the counter); the counter is guarded by a `threading.Lock` because the panel dispatches reviewers through a `ThreadPoolExecutor` (`engine.py:85-133`, default cap 8).
  - `def next_route_id(self) -> str` — charges ONE logical `route_chat` invocation against the ceiling and returns a fresh `uuid.uuid4().hex` route id. Raises `LaneCallCeilingExceeded` when the ceiling is already spent. Every lane call obtains its route id here, so the counter cannot be bypassed.
  - `def calls_used(self) -> int` — the count so far (for assertions/telemetry).
  - `def record_reroute(self, *, operation_id, lens, primary_route_id, fallback_route_id, exception_type, message) -> None` — appends the `ReviewRerouted` lane event (Task 1) via `lane_log.append(..., expected_revision=None)` with `event_id = derive_event_id(problem_id, f"reroute\x00{primary_route_id}")` (deterministic → an idempotent re-record is a no-op), `primary_profile="independent_review"`, `fallback_profile="deep_review"`, `relaxed_constraints=("family_independence", "snapshot_freshness")`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_route_context.py
import threading

import pytest

from llmxive.self_improvement.route_context import (
    LaneCallCeilingExceeded, LaneRouteContext, proposal_call_ceiling,
)

class _Sink:
    """A REAL in-memory RouteAudit double (no mock): records + always claims."""
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True

class _Budget:
    """A REAL in-memory ReservationAuthority double."""
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass

def _ctx(tmp_path, ceiling=4):
    return LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="reviewer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ceiling=ceiling,
    )

def test_proposal_ceiling_matches_the_spec_formula():
    # Policy Contract line 313: proposal run = 4N + R*(2N + 2); N=5, R=3 -> 56.
    assert proposal_call_ceiling(5, 3) == 56
    assert proposal_call_ceiling(1, 1) == 4 * 1 + 1 * (2 * 1 + 2)  # == 8

def test_route_ids_are_unique_and_charge_the_ceiling(tmp_path):
    ctx = _ctx(tmp_path, ceiling=3)
    ids = {ctx.next_route_id() for _ in range(3)}
    assert len(ids) == 3 and ctx.calls_used() == 3

def test_exceeding_the_ceiling_fails_closed(tmp_path):
    ctx = _ctx(tmp_path, ceiling=2)
    ctx.next_route_id(); ctx.next_route_id()
    with pytest.raises(LaneCallCeilingExceeded):
        ctx.next_route_id()

def test_ceiling_counter_is_thread_safe(tmp_path):
    # The panel dispatches reviewers through a ThreadPoolExecutor (engine.py:85-133),
    # so the counter must not over-admit under concurrency.
    ctx = _ctx(tmp_path, ceiling=20)
    got, lock = [], threading.Lock()

    def _take():
        try:
            rid = ctx.next_route_id()
            with lock:
                got.append(rid)
        except LaneCallCeilingExceeded:
            pass

    ts = [threading.Thread(target=_take) for _ in range(50)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert len(got) == 20 and len(set(got)) == 20  # exactly the ceiling, all unique

def test_hooks_are_required(tmp_path):
    # F2/F3: a lane context CANNOT be built without both the audit sink and the
    # reservation authority — there is no silently-unaudited/unbudgeted lane call.
    with pytest.raises(TypeError):
        LaneRouteContext(repo=tmp_path, problem_id="P1", attempt_id="A1", actor="a",
                         clock=lambda: "t", call_ceiling=4)  # missing both hooks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_route_context.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.self_improvement.route_context'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/route_context.py
"""What EVERY lane LLM call carries (FR-033a): the mandatory durable audit sink, the
Attempt credit authority, a minted route id, and the stage's logical-call ceiling.

The hooks are REQUIRED, not optional (maintainer review F2/F3): a lane call that skipped
either would be an unaudited routing decision or an unbudgeted paid dispatch. One context
is shared by a proposal review's whole panel AND its reviser, so the ceiling counter is
lock-guarded — the engine dispatches reviewers through a ``ThreadPoolExecutor``
(``engine.py:85-133``, default cap 8)."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.model_selection.attempt_hooks import ReservationAuthority, RouteAudit
from llmxive.self_improvement.events import Event, derive_event_id
from llmxive.self_improvement.lane_log import LaneLogConfig, append

#: The constraints the FR-002 fallback ALWAYS relaxes — factual (what changed), NOT a
#: causal claim about which one made the primary attempt fail (ModelUnavailable carries
#: only a textual reason and four documented causes).
RELAXED_CONSTRAINTS = ("family_independence", "snapshot_freshness")
PRIMARY_PROFILE = "independent_review"
FALLBACK_PROFILE = "deep_review"

class LaneCallCeilingExceeded(RuntimeError):
    """The stage's logical-``route_chat`` budget is exhausted (Policy Contract line 313).
    The Attempt fails closed — never a silent extra call."""

def proposal_call_ceiling(panel_size: int, max_rounds: int) -> int:
    """The PROPOSAL stage ceiling ``4N + R*(2N + 2)`` (Policy Contract line 313): every
    reviewer operation is up to TWO logical route_chat invocations (the FR-002 reroute),
    so each reviewer term doubles; the reviser's ``+2`` (producer — no independence, no
    reroute) does not."""
    return 4 * panel_size + max_rounds * (2 * panel_size + 2)

@dataclass
class LaneRouteContext:
    repo: Path
    problem_id: str
    attempt_id: str
    actor: str
    clock: Callable[[], str]
    route_audit: RouteAudit           # REQUIRED (F3) — mandatory durable sink
    reservation_authority: ReservationAuthority  # REQUIRED (F2) — Attempt budget gate
    call_ceiling: int
    config: LaneLogConfig = LaneLogConfig()
    _used: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def next_route_id(self) -> str:
        """Charge ONE logical route_chat invocation and mint its route id. Every lane call
        obtains its id here, so the ceiling cannot be bypassed."""
        with self._lock:
            if self._used >= self.call_ceiling:
                raise LaneCallCeilingExceeded(
                    f"attempt {self.attempt_id!r} exhausted its {self.call_ceiling} logical "
                    "route_chat invocations (Policy Contract line 313) — failing closed"
                )
            self._used += 1
        return uuid.uuid4().hex

    def calls_used(self) -> int:
        with self._lock:
            return self._used

    def record_reroute(self, *, operation_id: str, lens: str, primary_route_id: str,
                       fallback_route_id: str, exception_type: str, message: str) -> None:
        """Append the EXPLICIT ``ReviewRerouted`` record (F10) — the projection never has
        to infer a degradation from an accidental event pattern."""
        event = Event(
            event_id=derive_event_id(self.problem_id, f"reroute\x00{primary_route_id}"),
            event_type="ReviewRerouted", problem_id=self.problem_id, actor=self.actor,
            payload={
                "operation_id": operation_id, "lens": lens,
                "primary_profile": PRIMARY_PROFILE, "fallback_profile": FALLBACK_PROFILE,
                "primary_route_id": primary_route_id, "fallback_route_id": fallback_route_id,
                "primary_failure": {"exception_type": exception_type, "message": message},
                "relaxed_constraints": list(RELAXED_CONSTRAINTS),
            },
            timestamp=self.clock(), attempt_id=self.attempt_id,
        )
        append(self.repo, event, expected_revision=None, config=self.config)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_route_context.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/route_context.py tests/unit/test_self_improvement_route_context.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T2): LaneRouteContext — mandatory hooks, route-id minting, call ceiling"
```

---

### Task 3: Router plumbing — forward the five spec-025 params

**Files:**
- Modify: `src/llmxive/backends/router.py` (`_walker_route` lines 230-286; `chat_with_model_fallback` lines 289-317)
- Test: `tests/unit/test_router_lane_plumbing.py`

**Interfaces:**
- Produces (extended signatures — every new param defaults to a behavior-preserving no-op):
  - `chat_with_model_fallback(backend, messages, *, model, max_tokens=None, temperature=None, overrides=None, profile="standard_generation", independence_against=None, route_audit=None, reservation_authority=None, route_id=None, reraise_model_unavailable=False) -> ChatResponse` — forwards the five new params to `_walker_route`.
  - `_walker_route(..., independence_against=None, route_audit=None, reservation_authority=None, route_id=None, reraise_model_unavailable=False)` — forwards the first four to `route_chat` (which already accepts all of them, `route.py:244-265`) and **splits the exception handler**: `ModelUnavailable` propagates RAW when `reraise_model_unavailable=True` (the FR-002 reroute needs it), else converts to `BackendUnavailable` exactly as today; `ChainExhausted` ALWAYS converts to `BackendUnavailable` (a real outage — never a reroute trigger).
- **Not changed:** `reasoning_chat` (`router.py:320-349`) and `chat_with_fallback` (`router.py:352-407`) — they serve the research/paper pipeline, whose calls are not lane calls (see the scope boundary).
- Import note: `router.py` imports `model_selection` symbols **function-locally** (`router.py:265`, `router.py:391`) to avoid an import cycle. Keep that pattern — annotate the new params with STRING annotations (`"IndependenceBaseline | None"`, `"RouteAudit | None"`, `"ReservationAuthority | None"`); add NO module-top `model_selection` import.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_router_lane_plumbing.py
import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.backends.router import chat_with_model_fallback
from llmxive.model_selection.execute import ChainExhausted
from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable

class _Backend:
    name = "dartmouth"

class _Resp:
    text = "ok"

def _patch_route_chat(monkeypatch, fn):
    # route_chat is imported function-locally inside _walker_route, so patch it on the
    # module where it is DEFINED (that is the object the local import resolves to).
    monkeypatch.setattr("llmxive.model_selection.route.route_chat", fn)

def test_defaults_are_behavior_preserving(monkeypatch):
    seen = {}

    def _fake(messages, **kw):
        seen.update(kw)
        return _Resp()

    _patch_route_chat(monkeypatch, _fake)
    chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64, profile="deep_review")
    # the five new params arrive at route_chat as its own defaults (None) — unchanged path
    assert seen["independence_against"] is None
    assert seen["route_audit"] is None
    assert seen["reservation_authority"] is None
    assert seen["route_id"] is None

def test_all_five_params_are_forwarded(monkeypatch):
    seen = {}

    def _fake(messages, **kw):
        seen.update(kw)
        return _Resp()

    _patch_route_chat(monkeypatch, _fake)
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    sink, budget = object(), object()
    chat_with_model_fallback(
        _Backend(), [], model=None, max_tokens=64, profile="independent_review",
        independence_against=base, route_audit=sink, reservation_authority=budget, route_id="RID",
    )
    assert seen["independence_against"] is base
    assert seen["route_audit"] is sink
    assert seen["reservation_authority"] is budget
    assert seen["route_id"] == "RID"
    assert seen["profile"] == "independent_review"

def test_model_unavailable_converts_by_default_but_reraises_when_asked(monkeypatch):
    def _boom(messages, **kw):
        raise ModelUnavailable("no independent family live")

    _patch_route_chat(monkeypatch, _boom)
    # default: the existing outage-classification contract is preserved
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64, profile="independent_review")
    # the FR-002 reroute needs the RAW exception to trigger attempt 2
    with pytest.raises(ModelUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)

def test_chain_exhausted_always_converts_even_when_reraise_is_set(monkeypatch):
    # ChainExhausted is a real outage (the chain RAN and none succeeded) — it must NEVER
    # become a reroute trigger, even for a caller that asked for raw ModelUnavailable.
    def _boom(messages, **kw):
        raise ChainExhausted("every candidate advanced")

    _patch_route_chat(monkeypatch, _boom)
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Backend(), [], model=None, max_tokens=64,
                                 profile="independent_review", reraise_model_unavailable=True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_router_lane_plumbing.py -q`
Expected: FAIL — `TypeError: chat_with_model_fallback() got an unexpected keyword argument 'independence_against'`.

- [ ] **Step 3: Write minimal implementation**

Replace `chat_with_model_fallback`'s signature + body (keeping its docstring, extended with a sentence naming the five new params as spec-025 lane plumbing):

```python
def chat_with_model_fallback(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: "IndependenceBaseline | None" = None,
    route_audit: "RouteAudit | None" = None,
    reservation_authority: "ReservationAuthority | None" = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
) -> ChatResponse:
    return _walker_route(
        backend, messages, model=model,
        max_tokens=REASONING_MAX_TOKENS if max_tokens is None else max_tokens,
        temperature=temperature, overrides=overrides, profile=profile,
        independence_against=independence_against, route_audit=route_audit,
        reservation_authority=reservation_authority, route_id=route_id,
        reraise_model_unavailable=reraise_model_unavailable,
    )
```

Replace `_walker_route`'s signature + the `route_chat` call + the except block (keep the rest of the docstring/body):

```python
def _walker_route(
    backend: BaseBackend,
    messages: Iterable[ChatMessage],
    *,
    model: str | None,
    max_tokens: int,
    temperature: float | None,
    overrides: RequirementOverrides | None = None,
    profile: str = "standard_generation",
    independence_against: "IndependenceBaseline | None" = None,
    route_audit: "RouteAudit | None" = None,
    reservation_authority: "ReservationAuthority | None" = None,
    route_id: str | None = None,
    reraise_model_unavailable: bool = False,
) -> ChatResponse:
    from llmxive.model_selection.execute import ChainExhausted
    from llmxive.model_selection.route import route_chat
    from llmxive.model_selection.types import ModelUnavailable

    injected_name = getattr(backend, "name", None) or "dartmouth"

    def factory(name: str) -> BaseBackend:
        return backend if name == injected_name else make_backend(name)

    try:
        return route_chat(
            messages, profile=profile, caller_model=model, max_tokens=max_tokens,
            temperature=temperature, backend_factory=factory, overrides=overrides,
            independence_against=independence_against, route_audit=route_audit,
            reservation_authority=reservation_authority, route_id=route_id,
        )
    except ModelUnavailable as exc:
        # Spec 025 FR-002: the proposal reroute needs the RAW ModelUnavailable to trigger
        # its second attempt. Every other caller keeps the outage-classification contract.
        if reraise_model_unavailable:
            raise
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc
    except ChainExhausted as exc:
        # ALWAYS a clean run-loop abort — the chain ran and none succeeded. Never a
        # reroute trigger, even when reraise_model_unavailable is set.
        raise BackendUnavailable(
            f"model selection/execution produced no usable candidate "
            f"(outage or ineligible): {exc}"
        ) from exc
```

- [ ] **Step 4: Run test to verify it passes + confirm no regression**

Run: `pytest tests/unit/test_router_lane_plumbing.py -q`
Expected: PASS (4 passed).

Run: `pytest tests/unit -k "router or walker or reviewer" -q`
Expected: PASS — the default path is byte-for-byte unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/backends/router.py tests/unit/test_router_lane_plumbing.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T3): plumb independence/audit/authority/route_id + raw-ModelUnavailable through the router"
```

---

### Task 4: `LLMReviewer` — lane context + two-attempt independence reroute

**Files:**
- Modify: `src/llmxive/convergence/llm_reviewer.py` (`_STAGE_PREFIX` ~lines 100-147; `LLMReviewer.__init__` lines 819-877; `_call_backend` lines 1148-1167)
- Test: `tests/unit/test_llm_reviewer_reroute.py`

**Interfaces:**
- Consumes: `LaneRouteContext` (Task 2); `chat_with_model_fallback` with the five new params (Task 3); `IndependenceBaseline`, `ModelUnavailable` (`model_selection.types`).
- Produces:
  - `_STAGE_PREFIX` gains `"self_improvement_proposal": "si_proposal"` → the lane's per-lens prompt path becomes `<repo_root>/agents/prompts/panels/panel_si_proposal_<lens>.md` (`_prompt_path_for`, `llm_reviewer.py:150-165`). Without this entry `_prompt_path_for` raises `ValueError("unknown stage ...")` and a lane reviewer cannot be constructed at all.
  - `LLMReviewer.__init__` gains three keyword params, all defaulting to `None` so every existing call site is byte-for-byte unchanged: `route_context: "LaneRouteContext | None" = None`, `independence_against: "IndependenceBaseline | None" = None`, `fallback_profile: str | None = None`. Stored as `self._route_context`, `self._independence_against`, `self._fallback_profile`.
  - `_call_backend(self, messages) -> str` — when `self._route_context is None`, the EXISTING single unrouted call, unchanged. Otherwise delegates to `_route_review`.
  - `_route_review(self, messages) -> str` — the lane path:
    1. `primary_route_id = ctx.next_route_id()` (charges the ceiling);
    2. attempt 1 = `chat_with_model_fallback(..., profile=self._profile, independence_against=self._independence_against, route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority, route_id=primary_route_id, reraise_model_unavailable=bool(self._fallback_profile))`;
    3. on `ModelUnavailable` **and** `self._fallback_profile is not None` → `fallback_route_id = ctx.next_route_id()`; `ctx.record_reroute(...)` (the explicit `ReviewRerouted` event, F10); attempt 2 = same call with `profile=self._fallback_profile`, **no** `independence_against`, and `reraise_model_unavailable=False` (a fallback that ALSO finds nothing is a genuine outage → `BackendUnavailable` → the engine's clean-abort path, not a second degrade).
    - With `fallback_profile=None` (the future **patch** review's fail-closed binding), `reraise_model_unavailable` is `False`, so a `ModelUnavailable` converts to `BackendUnavailable` and the run aborts — no promotion. The same class serves both bindings.
  - `operation_id` = the `primary_route_id` (unique per reviewer operation; makes the `ReviewRerouted` `event_id` deterministic for an idempotent re-record).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_llm_reviewer_reroute.py
from pathlib import Path

import pytest

from llmxive.model_selection.types import IndependenceBaseline, ModelUnavailable
from llmxive.self_improvement.route_context import LaneRouteContext

LENS = "worthwhile-improvement"
STAGE = "self_improvement_proposal"

class _Sink:
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True

class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass

@pytest.fixture
def repo_root(tmp_path):
    # REAL prompt files at the convention path (no mock): _load_system_prompt reads the
    # per-lens prompt + the SSoT shared block, so both must exist.
    panels = tmp_path / "agents" / "prompts" / "panels"
    panels.mkdir(parents=True)
    (panels / f"panel_si_proposal_{LENS}.md").write_text("# Panel Reviewer — lens\n\n## Lens\nJudge it.\n")
    shared = tmp_path / "agents" / "prompts" / "_shared"
    shared.mkdir(parents=True)
    (shared / "panel_review_block.md").write_text("## Output format\nUse the protocol.\n")
    return tmp_path

def _ctx(repo_root, ceiling=10):
    return LaneRouteContext(
        repo=repo_root, problem_id="P1", attempt_id="A1", actor="reviewer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ceiling=ceiling,
    )

def _reviewer(repo_root, **kw):
    from llmxive.convergence.llm_reviewer import LLMReviewer
    return LLMReviewer(lens=LENS, stage=STAGE, backend=object(), repo_root=Path(repo_root), **kw)

def test_no_context_uses_the_unchanged_single_call(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        class R: text = "plain"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    r = _reviewer(repo_root, profile="deep_review")
    assert r._call_backend([]) == "plain"
    assert len(calls) == 1
    # the legacy path passes NO lane params
    assert calls[0].get("route_audit") is None and calls[0].get("route_id") is None

def test_reroute_records_an_explicit_event_and_uses_two_route_ids(repo_root, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        if kw["profile"] == "independent_review":
            raise ModelUnavailable("no independent family live")
        class R: text = "fallback-body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    recorded = []
    ctx.record_reroute = lambda **kw: recorded.append(kw)  # capture the explicit record
    base = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=base, route_context=ctx)

    assert r._call_backend([]) == "fallback-body"
    assert len(calls) == 2
    # attempt 1: constrained + raw-ModelUnavailable enabled; hooks present
    assert calls[0]["profile"] == "independent_review"
    assert calls[0]["independence_against"] is base
    assert calls[0]["reraise_model_unavailable"] is True
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    # attempt 2: unconstrained, must NOT re-raise (a second miss is a real outage)
    assert calls[1]["profile"] == "deep_review"
    assert calls[1].get("independence_against") is None
    assert calls[1]["reraise_model_unavailable"] is False
    # DISTINCT route ids, both charged against the ceiling
    assert calls[0]["route_id"] != calls[1]["route_id"]
    assert ctx.calls_used() == 2
    # the degradation is recorded EXPLICITLY (F10), not left to be inferred
    assert len(recorded) == 1
    assert recorded[0]["lens"] == LENS
    assert recorded[0]["primary_route_id"] == calls[0]["route_id"]
    assert recorded[0]["fallback_route_id"] == calls[1]["route_id"]
    assert recorded[0]["exception_type"] == "ModelUnavailable"

def test_successful_primary_never_reroutes_or_records(repo_root, monkeypatch):
    def _fake(backend, messages, **kw):
        class R: text = "independent-body"
        return R()

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    recorded = []
    ctx.record_reroute = lambda **kw: recorded.append(kw)
    r = _reviewer(repo_root, profile="independent_review", fallback_profile="deep_review",
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=ctx)
    assert r._call_backend([]) == "independent-body"
    assert recorded == [] and ctx.calls_used() == 1

def test_without_a_fallback_profile_model_unavailable_is_not_rerouted(repo_root, monkeypatch):
    # The future PATCH binding: required independence, NO fallback → fail closed.
    def _fake(backend, messages, **kw):
        assert kw["reraise_model_unavailable"] is False  # converts to BackendUnavailable
        raise ModelUnavailable("no independent family live")

    monkeypatch.setattr("llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake)
    ctx = _ctx(repo_root)
    r = _reviewer(repo_root, profile="independent_review", fallback_profile=None,
                  independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
                  route_context=ctx)
    with pytest.raises(ModelUnavailable):
        r._call_backend([])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_llm_reviewer_reroute.py -q`
Expected: FAIL — `ValueError: unknown stage 'self_improvement_proposal'` (the `_STAGE_PREFIX` gap) or `TypeError: __init__() got an unexpected keyword argument 'route_context'`.

- [ ] **Step 3: Write minimal implementation**

Add the lane stage to `_STAGE_PREFIX` (`llm_reviewer.py` ~lines 100-147):

```python
    # Spec 025 slice 1B: the self-improvement lane's proposal review. Its per-lens
    # prompts live at agents/prompts/panels/panel_si_proposal_<lens>.md.
    "self_improvement_proposal": "si_proposal",
```

Add the three params to `LLMReviewer.__init__` (after `overrides`) and store them:

```python
        # Spec 025 slice 1B: the lane's mandatory routing context (audit sink + Attempt
        # credit authority + route-id/ceiling). None = a NON-lane reviewer (research /
        # paper panels), whose call path stays byte-for-byte unchanged.
        route_context: "LaneRouteContext | None" = None,
        # FR-002: the producer baseline this lens must differ from, and the profile to
        # degrade to when no independent family is selectable. fallback_profile=None
        # means FAIL CLOSED (the patch-review binding).
        independence_against: "IndependenceBaseline | None" = None,
        fallback_profile: str | None = None,
    ) -> None:
        ...  # existing assignments unchanged
        self._route_context = route_context
        self._independence_against = independence_against
        self._fallback_profile = fallback_profile
```

Replace `_call_backend` and add `_route_review` (keep the existing docstring on the legacy branch):

```python
    def _call_backend(self, messages: list[ChatMessage]) -> str:
        if self._route_context is not None:
            return self._route_review(messages)
        response = chat_with_model_fallback(
            self._backend, messages, model=None, max_tokens=self._max_tokens,
            temperature=self._temperature, overrides=self._overrides, profile=self._profile,
        )
        return getattr(response, "text", "") or ""

    def _route_review(self, messages: list[ChatMessage]) -> str:
        """The lane path (spec 025 FR-002): every call carries the mandatory audit sink +
        Attempt credit authority, and a proposal lens performs the TWO-ATTEMPT reroute —
        ``independent_review`` (required family) first, then, on a raw ``ModelUnavailable``,
        ``deep_review`` with an EXPLICIT ``ReviewRerouted`` record. No new profile is
        introduced; both are delivered 026 profiles."""
        from llmxive.model_selection.types import ModelUnavailable

        ctx = self._route_context
        assert ctx is not None  # guarded by the caller
        primary_route_id = ctx.next_route_id()
        try:
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides, profile=self._profile,
                independence_against=self._independence_against,
                route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
                route_id=primary_route_id,
                # Only a lens WITH a fallback needs the raw exception; a fail-closed lens
                # (patch review) keeps the standard BackendUnavailable conversion.
                reraise_model_unavailable=self._fallback_profile is not None,
            )
        except ModelUnavailable as exc:
            if self._fallback_profile is None:
                raise
            fallback_route_id = ctx.next_route_id()
            ctx.record_reroute(
                operation_id=primary_route_id, lens=self._lens,
                primary_route_id=primary_route_id, fallback_route_id=fallback_route_id,
                exception_type=type(exc).__name__, message=str(exc),
            )
            response = chat_with_model_fallback(
                self._backend, messages, model=None, max_tokens=self._max_tokens,
                temperature=self._temperature, overrides=self._overrides,
                profile=self._fallback_profile,  # no independence constraint on the fallback
                route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
                route_id=fallback_route_id,
                # A fallback that ALSO finds nothing is a genuine outage, not a second
                # degrade → let it convert to BackendUnavailable (engine clean-abort).
            )
        return getattr(response, "text", "") or ""
```

(`LaneRouteContext`/`IndependenceBaseline` appear only in STRING annotations, so no module-top import is added — matching the file's existing function-local `model_selection` import discipline.)

- [ ] **Step 4: Run test to verify it passes + confirm no regression**

Run: `pytest tests/unit/test_llm_reviewer_reroute.py -q`
Expected: PASS (4 passed).

Run: `pytest tests/unit -k llm_reviewer -q`
Expected: PASS — the non-lane path is unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/llm_reviewer.py tests/unit/test_llm_reviewer_reroute.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T4): LLMReviewer lane context + two-attempt reroute with explicit ReviewRerouted"
```

---

### Task 5: `LaneProposalReviser` — the routed, single-call reviser

**Files:**
- Create: `src/llmxive/convergence/lane_reviser.py`
- Test: `tests/unit/test_lane_reviser.py`

**Interfaces:**
- Consumes: `LaneRouteContext` (Task 2); `chat_with_model_fallback` (Task 3); `Concern`, `ConcernResponse` (`convergence.types`).
- Produces:
  - `class LaneProposalReviser` — structurally conforms to `convergence.types.Reviser`: `revise(self, artifacts: dict[str, str], concerns: list[Concern]) -> tuple[dict[str, str], list[ConcernResponse]]`.
  - Constructor: `LaneProposalReviser(*, backend, route_context: LaneRouteContext, artifact_key: str = "proposal.md", profile: str = "deep_code", max_tokens: int = 32_768, temperature: float = 0.0)`.
  - **Exactly ONE `chat_with_model_fallback` call per `revise()`** (the ceiling's `+2`-per-round term is the ENGINE's malformed-reply retry, `engine.py:521-533` — not an internal self-consistency loop). It does NOT use `invoke_reviser_backend`/`run_with_self_consistency`, which would make up to three calls per `revise()`.
  - It carries the lane context on every call: `route_audit`, `reservation_authority`, and a `route_id` from `ctx.next_route_id()`. It passes **no** `independence_against` (the producer has no independence constraint) and no `fallback_profile` (no reroute — hence the ceiling's `+2` is not doubled).
  - Response contract: the model returns ONE fenced ```json block: `{"proposal": "<full revised proposal markdown>", "responses": [{"concern_id": "...", "response": "...", "what_changed": "..."}]}`. `_parse_response` raises on a missing/unparseable block or a missing concern id, so the engine's retry produces the second attempt.

- [ ] **Step 0 (do first): match the engine's malformed-reply retry.** Read `src/llmxive/convergence/engine.py:518-553` and note the EXACT exception type(s) the reviser retry loop catches. `_parse_response` MUST raise one of those (so a malformed reply produces the engine's second attempt rather than aborting the run). Record the type in the module docstring.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_lane_reviser.py
import json

import pytest

from llmxive.convergence.types import Concern
from llmxive.self_improvement.route_context import LaneRouteContext

class _Sink:
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True

class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass

def _ctx(tmp_path, ceiling=10):
    return LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="proposer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ceiling=ceiling,
    )

def _concern(cid="c1"):
    return Concern(id=cid, reviewer="worthwhile-improvement", severity="requirement",
                   artifact="proposal.md", text="Blast radius is unbounded.")

def _body(proposal="# Revised\n\nScoped to one module.", cid="c1"):
    payload = {"proposal": proposal,
               "responses": [{"concern_id": cid, "response": "Scoped it.",
                              "what_changed": "Added a blast-radius section."}]}
    return "```json\n" + json.dumps(payload) + "\n```"

def test_revise_makes_exactly_one_routed_call_with_the_lane_hooks(tmp_path, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)
        class R: text = _body()
        return R()

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    ctx = _ctx(tmp_path)
    rev = LaneProposalReviser(backend=object(), route_context=ctx)

    updated, responses = rev.revise({"proposal.md": "# Original"}, [_concern()])

    # ONE call — NOT the 3-call self-consistency path (that would break the ceiling's +2).
    assert len(calls) == 1 and ctx.calls_used() == 1
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    assert calls[0]["route_id"]
    assert calls[0].get("independence_against") is None  # the producer has no constraint
    assert updated["proposal.md"].startswith("# Revised")
    assert [r.concern_id for r in responses] == ["c1"]

def test_every_concern_must_be_answered(tmp_path, monkeypatch):
    def _fake(backend, messages, **kw):
        class R: text = _body(cid="WRONG-ID")  # answers a concern that was not raised
        return R()

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    rev = LaneProposalReviser(backend=object(), route_context=_ctx(tmp_path))
    with pytest.raises(ValueError):  # match the engine's malformed-reply type (Step 0)
        rev.revise({"proposal.md": "# Original"}, [_concern()])

def test_unparseable_reply_raises_for_the_engine_retry(tmp_path, monkeypatch):
    def _fake(backend, messages, **kw):
        class R: text = "no json block here"
        return R()

    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", _fake)
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    rev = LaneProposalReviser(backend=object(), route_context=_ctx(tmp_path))
    with pytest.raises(ValueError):
        rev.revise({"proposal.md": "# Original"}, [_concern()])

def test_conforms_to_the_reviser_protocol(tmp_path):
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    from llmxive.convergence.types import Reviser
    assert isinstance(LaneProposalReviser(backend=object(), route_context=_ctx(tmp_path)), Reviser)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_lane_reviser.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.convergence.lane_reviser'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/convergence/lane_reviser.py
"""The self-improvement lane's proposal reviser (spec 025 FR-019): the proposer
addressing the panel's concerns inside the shared ``run_convergence`` loop.

Deliberately NOT built on ``invoke_reviser_backend``/``run_with_self_consistency``
(``revisers/_self_consistency.py``): that path makes up to THREE LLM calls per
``revise()``, which would break the documented proposal ceiling ``4N + R*(2N + 2)``
whose ``+2`` models the ENGINE's at-most-two reviser attempts per round
(``engine.py:521-533``). This reviser makes EXACTLY ONE routed call per ``revise()``
and raises on a malformed reply so the engine's own retry provides the second attempt.

Every call carries the lane's mandatory audit sink + Attempt credit authority (F2/F3):
the reviser is a lane LLM call like any other, and its spend counts against the Attempt."""

from __future__ import annotations

import json
import re

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_model_fallback
from llmxive.convergence.types import Concern, ConcernResponse
from llmxive.self_improvement.route_context import LaneRouteContext

_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

_SYSTEM = (
    "You are the author of a self-improvement proposal for an autonomous research "
    "platform. A review panel raised concerns. Revise the proposal so every concern is "
    "addressed, and report what you changed.\n\n"
    "Reply with EXACTLY ONE fenced ```json block and nothing else:\n"
    '{"proposal": "<the FULL revised proposal markdown>", '
    '"responses": [{"concern_id": "<id>", "response": "<how you addressed it>", '
    '"what_changed": "<the concrete edit>"}]}\n\n'
    "Answer EVERY concern id exactly once. Do not invent concern ids."
)

class LaneProposalReviser:
    """Conforms structurally to :class:`llmxive.convergence.types.Reviser`."""

    def __init__(self, *, backend: object, route_context: LaneRouteContext,
                 artifact_key: str = "proposal.md", profile: str = "deep_code",
                 max_tokens: int = 32_768, temperature: float = 0.0) -> None:
        self._backend = backend
        self._route_context = route_context
        self._artifact_key = artifact_key
        self._profile = profile
        self._max_tokens = max_tokens
        self._temperature = temperature

    def revise(self, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        ctx = self._route_context
        messages = [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=self._compose(artifacts, concerns)),
        ]
        response = chat_with_model_fallback(
            self._backend, messages, model=None, max_tokens=self._max_tokens,
            temperature=self._temperature, profile=self._profile,
            route_audit=ctx.route_audit, reservation_authority=ctx.reservation_authority,
            route_id=ctx.next_route_id(),
        )
        return self._parse(getattr(response, "text", "") or "", artifacts, concerns)

    def _compose(self, artifacts: dict[str, str], concerns: list[Concern]) -> str:
        body = artifacts.get(self._artifact_key, "")
        listed = "\n".join(
            f"- [{c.id}] ({c.severity}) {c.artifact}: {c.text}" for c in concerns
        )
        return f"## Current proposal\n\n{body}\n\n## Concerns to address\n\n{listed}\n"

    def _parse(self, text: str, artifacts: dict[str, str], concerns: list[Concern],
               ) -> tuple[dict[str, str], list[ConcernResponse]]:
        match = _JSON_BLOCK.search(text)
        if match is None:
            raise ValueError("lane reviser reply has no fenced ```json block")
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(f"lane reviser reply is not valid JSON: {exc}") from exc
        proposal = payload.get("proposal")
        if not isinstance(proposal, str) or not proposal.strip():
            raise ValueError("lane reviser reply is missing a non-empty 'proposal'")
        answered = {r.get("concern_id") for r in payload.get("responses", [])}
        expected = {c.id for c in concerns}
        if answered != expected:
            raise ValueError(
                f"lane reviser answered {sorted(answered)!r}, expected exactly {sorted(expected)!r}"
            )
        responses = [
            ConcernResponse(
                concern_id=r["concern_id"], response=r.get("response", ""),
                what_changed=r.get("what_changed", ""), artifacts_changed=[self._artifact_key],
            )
            for r in payload["responses"]
        ]
        updated = dict(artifacts)
        updated[self._artifact_key] = proposal
        return updated, responses
```

(Confirm `ConcernResponse`'s exact field set against `convergence/types.py:169-197` while implementing; supply any additional required field with its documented default.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_lane_reviser.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/lane_reviser.py tests/unit/test_lane_reviser.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T5): LaneProposalReviser — one routed call per revise, lane hooks carried"
```

---

### Task 6: Complete `InvocationIdentity` from the explicit events

**Files:**
- Create: `src/llmxive/self_improvement/invocation_identity.py`
- Test: `tests/unit/test_self_improvement_invocation_identity.py`

**Interfaces:**
- Consumes: lane `Event`s (Slice 1A) — the audit events `EventStoreRouteAudit` recorded, plus `ReviewRerouted` (Task 1).
- Produces:
  - `@dataclass(frozen=True) class IndependenceDegraded`: `primary_profile: str`, `fallback_profile: str`, `primary_failure: Mapping[str, str]` (`{exception_type, message}`), `relaxed_constraints: tuple[str, ...]`.
  - `@dataclass(frozen=True) class InvocationIdentity` — the Key-Entities field set (spec line 227) PLUS the provenance the maintainer review required: `actor_instance_id: str`, `model: str`, `backend: str`, `serving_endpoint: str`, `vendor: str`, `family: str`, `prompt_digest: str`, `context_digest: str`, `selection_policy_version: int`, `snapshot_digest: str`, `snapshot_provenance: Mapping[str, Mapping[str, object]]`, `route_outcome: str`, `degradation: IndependenceDegraded | None = None`. (`serving_endpoint`, `vendor`, and `snapshot_provenance` are what make "reproduce *why that model was chosen*" actually checkable.)
  - `build_invocation_identity(events: list[Event], *, route_id: str) -> InvocationIdentity | None` — from the events whose `payload["route_id"] == route_id`: the `ChainResolved` supplies the digests, `selection_policy_version`, `snapshot_digest`, `snapshot_provenance`; the `DispatchCompleted` supplies the `candidate` that ACTUALLY ran (model/backend/serving_endpoint/vendor/family); `actor_instance_id = route_id`. `route_outcome` is `"independence_degraded"` **iff a `ReviewRerouted` event names this `route_id` as its `fallback_route_id`** — read from the EXPLICIT record (F10), never inferred from a `SelectionFailure`+success coincidence. Returns `None` when there is no `ChainResolved`+`DispatchCompleted` pair (nothing ran → a failed logical call, no identity).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_invocation_identity.py
from llmxive.self_improvement.events import Event
from llmxive.self_improvement.invocation_identity import build_invocation_identity

_REF = {"backend": "dartmouth", "serving_endpoint": "dartmouth", "model_id": "gemma-3-27b",
        "model_family": "gemma", "vendor": "google"}
_PROV = {"catalog": {"source": "live", "observed_at": "2026-07-25T00:00:00+00:00", "age_s": 0.0}}

def _ev(etype, payload, eid):
    return Event(event_id=eid, event_type=etype, problem_id="P1", actor="a", payload=payload,
                 timestamp="2026-07-25T00:00:00+00:00", attempt_id="A1",
                 expected_problem_revision=0, seq=0)

def _chain(route_id):
    return _ev("ChainResolved", {"route_id": route_id, "prompt_digest": "pd", "context_digest": "cd",
                                 "snapshot_digest": "sd", "selection_policy_version": 3,
                                 "snapshot_provenance": _PROV, "candidates": [_REF]}, "c")

def _done(route_id):
    return _ev("DispatchCompleted", {"route_id": route_id, "candidate_index": 0,
                                     "candidate": _REF, "reservation_id": None}, "d")

def _rerouted(primary, fallback):
    return _ev("ReviewRerouted", {
        "operation_id": primary, "lens": "worthwhile-improvement",
        "primary_profile": "independent_review", "fallback_profile": "deep_review",
        "primary_route_id": primary, "fallback_route_id": fallback,
        "primary_failure": {"exception_type": "ModelUnavailable", "message": "none live"},
        "relaxed_constraints": ["family_independence", "snapshot_freshness"]}, "rr")

def test_success_identity_carries_full_selection_provenance():
    ii = build_invocation_identity([_chain("R"), _done("R")], route_id="R")
    assert ii is not None
    assert (ii.model, ii.family, ii.backend) == ("gemma-3-27b", "gemma", "dartmouth")
    assert (ii.serving_endpoint, ii.vendor) == ("dartmouth", "google")   # reproduce WHY
    assert ii.snapshot_provenance == _PROV
    assert (ii.prompt_digest, ii.context_digest, ii.snapshot_digest) == ("pd", "cd", "sd")
    assert ii.selection_policy_version == 3
    assert ii.route_outcome == "success" and ii.degradation is None
    assert ii.actor_instance_id == "R"

def test_degradation_comes_from_the_explicit_reroute_event():
    # The FALLBACK leg's route_id is what ran; the explicit ReviewRerouted event names it.
    events = [_rerouted("R1", "R2"), _chain("R2"), _done("R2")]
    ii = build_invocation_identity(events, route_id="R2")
    assert ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == "independent_review"
    assert ii.degradation.fallback_profile == "deep_review"
    assert ii.degradation.primary_failure["exception_type"] == "ModelUnavailable"
    assert ii.degradation.relaxed_constraints == ("family_independence", "snapshot_freshness")

def test_a_selection_failure_alone_does_not_imply_degradation():
    # F10: no inference from an event PATTERN — without an explicit ReviewRerouted record
    # naming this route as the fallback leg, the outcome is a plain success.
    sf = _ev("SelectionFailure", {"route_id": "R", "exception_type": "ModelUnavailable",
                                  "message": "x", "requirement_digest": "rq",
                                  "snapshot_provenance": _PROV}, "s")
    ii = build_invocation_identity([sf, _chain("R"), _done("R")], route_id="R")
    assert ii.route_outcome == "success" and ii.degradation is None

def test_no_dispatch_yields_no_identity():
    assert build_invocation_identity([_chain("R")], route_id="R") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: FAIL — `ModuleNotFoundError: ... invocation_identity`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/self_improvement/invocation_identity.py
"""The audit-derived ``InvocationIdentity`` (spec 025 Key Entities line 227) — sourced
ENTIRELY from the lane's durable audit events for one ``route_id``, because
``route_chat``'s bare ``ChatResponse`` carries none of it.

``route_outcome`` is read from the EXPLICIT ``ReviewRerouted`` record (maintainer review
F10) — never inferred from a "SelectionFailure + success" event pattern, which could
coincide for unrelated reasons."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from llmxive.self_improvement.events import Event

@dataclass(frozen=True)
class IndependenceDegraded:
    primary_profile: str
    fallback_profile: str
    primary_failure: Mapping[str, str]
    relaxed_constraints: tuple[str, ...]

@dataclass(frozen=True)
class InvocationIdentity:
    actor_instance_id: str
    model: str
    backend: str
    serving_endpoint: str
    vendor: str
    family: str
    prompt_digest: str
    context_digest: str
    selection_policy_version: int
    snapshot_digest: str
    snapshot_provenance: Mapping[str, Mapping[str, object]]
    route_outcome: str
    degradation: IndependenceDegraded | None = None

def build_invocation_identity(events: list[Event], *, route_id: str) -> InvocationIdentity | None:
    scoped = [e for e in events if e.payload.get("route_id") == route_id]
    chain = next((e for e in scoped if e.event_type == "ChainResolved"), None)
    completed = next((e for e in scoped if e.event_type == "DispatchCompleted"), None)
    if chain is None or completed is None:
        return None  # nothing actually ran → a failed logical call, no identity
    rerouted = next(
        (e for e in events
         if e.event_type == "ReviewRerouted" and e.payload.get("fallback_route_id") == route_id),
        None,
    )
    if rerouted is None:
        outcome, degradation = "success", None
    else:
        p = rerouted.payload
        outcome = "independence_degraded"
        degradation = IndependenceDegraded(
            primary_profile=p["primary_profile"], fallback_profile=p["fallback_profile"],
            primary_failure=p["primary_failure"],
            relaxed_constraints=tuple(p["relaxed_constraints"]),
        )
    ref, cp = completed.payload["candidate"], chain.payload
    return InvocationIdentity(
        actor_instance_id=route_id, model=ref["model_id"], backend=ref["backend"],
        serving_endpoint=ref["serving_endpoint"], vendor=ref["vendor"], family=ref["model_family"],
        prompt_digest=cp["prompt_digest"], context_digest=cp["context_digest"],
        selection_policy_version=int(cp["selection_policy_version"]),
        snapshot_digest=cp["snapshot_digest"], snapshot_provenance=cp.get("snapshot_provenance", {}),
        route_outcome=outcome, degradation=degradation,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_invocation_identity.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/self_improvement/invocation_identity.py tests/unit/test_self_improvement_invocation_identity.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T6): complete InvocationIdentity from explicit audit + reroute events"
```

---

### Task 7: Proposal lens prompts + `build_proposal_review_spec`

**Files:**
- Create: `agents/prompts/panels/panel_si_proposal_worthwhile-improvement.md`, `..._diagnosis-correctness.md`, `..._tractability.md`, `..._testability.md`, `..._blast-radius-sanity.md`
- Create: `src/llmxive/convergence/self_improvement_specs.py`
- Test: `tests/unit/test_self_improvement_review_spec.py`

**Interfaces:**
- Consumes: `LLMReviewer` with the lane params (Task 4); `LaneProposalReviser` (Task 5); `LaneRouteContext` + `proposal_call_ceiling` (Task 2); `ReviewSpec` (`convergence/types.py:295-313`).
- Produces:
  - `PROPOSAL_STAGE = "self_improvement_proposal"` (matches the `_STAGE_PREFIX` entry from Task 4).
  - `PROPOSAL_LENSES: tuple[str, ...] = ("worthwhile-improvement", "diagnosis-correctness", "tractability", "testability", "blast-radius-sanity")` — the exact lens set from the Self-improvement ReviewSpec table (spec line 278).
  - `PROPOSAL_MAX_ROUNDS = 3` (table line 281 — the engine default).
  - `build_proposal_review_spec(*, backend, repo_root: Path, proposer_baseline: IndependenceBaseline, route_context: LaneRouteContext, artifact_key: str = "proposal.md") -> ReviewSpec` — **`route_context` is REQUIRED** (F3: no silently-unaudited panel). Builds one `LLMReviewer` per lens with `stage=PROPOSAL_STAGE`, `profile="independent_review"`, `fallback_profile="deep_review"`, `independence_against=proposer_baseline`, `route_context=route_context`; the `reviser` is a `LaneProposalReviser` sharing the SAME context (so its spend and provenance land on the same Attempt); `max_rounds=PROPOSAL_MAX_ROUNDS`. Every required `ReviewSpec` field is supplied.

- [ ] **Step 0 (do first): match the ReviewSpec conventions + author the prompts.**
  (a) Read `src/llmxive/convergence/reviewspecs.py`'s `build_research_review_reviewspec` (lines 733-757) for the house convention of `kickback_routing` and `overflow_goal`, and read the `Severity` type in `convergence/types.py`. The proposal review's non-convergence outcome is `rejected` (pre-claim — spec transition table line 245), so map EVERY `Severity` member to `"rejected"` and give `overflow_goal` the same short-phrase shape the research builder uses.
  (b) Author the 5 lens prompts at the paths above, matching the house structure verified in `agents/prompts/panels/panel_spec_requirements_coverage.md`: `# Panel Reviewer — <lens> (Self-improvement proposal stage)`, then `## Lens` (the bulk — the rule, edge cases, what NOT to flag, concrete examples of what satisfies it), `## Inputs` (terse), `## Output format` (defer to `[_shared/panel_review_block.md](../_shared/panel_review_block.md)` + a one-line severity hint). Lens intents: **worthwhile-improvement** (is this change worth making at all — real recurring pain, not a nit); **diagnosis-correctness** (does the proposal's causal story actually explain the cited evidence); **tractability** (can this be implemented + evaluated within the Attempt's budget/blast-radius envelope); **testability** (is there a concrete failing-at-base / passing-at-head signal, not just "tests pass"); **blast-radius-sanity** (is the proposed surface narrow, reversible, and outside the protected model-execution surface).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_self_improvement_review_spec.py
from pathlib import Path

import pytest

from llmxive.convergence.self_improvement_specs import (
    PROPOSAL_LENSES, PROPOSAL_MAX_ROUNDS, PROPOSAL_STAGE, build_proposal_review_spec,
)
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.route_context import LaneRouteContext, proposal_call_ceiling

class _Sink:
    def record(self, event) -> None: ...
    def claim_dispatch(self, event) -> bool: return True

class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool: return True
    def release(self, reservation_id) -> None: ...
    def mark_retained(self, reservation_id) -> None: ...

def _ctx(tmp_path):
    return LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(),
        call_ceiling=proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS),
    )

def test_spec_wires_every_lens_with_the_reroute_and_the_shared_context(tmp_path):
    # Uses the REAL repo prompts (repo_root=the actual repo), so a missing/misnamed
    # prompt file fails this test rather than surfacing at runtime.
    baseline = IndependenceBaseline(families=frozenset({"qwen3.5"}))
    ctx = _ctx(tmp_path)
    spec = build_proposal_review_spec(
        backend=object(), repo_root=Path("."), proposer_baseline=baseline, route_context=ctx,
    )
    assert spec.stage == PROPOSAL_STAGE and spec.max_rounds == PROPOSAL_MAX_ROUNDS
    assert tuple(r.name for r in spec.reviewers) == PROPOSAL_LENSES
    for r in spec.reviewers:
        assert r._profile == "independent_review" and r._fallback_profile == "deep_review"
        assert r._independence_against is baseline
        assert r._route_context is ctx          # the SAME context across the panel
    # the reviser shares the context too (F3: its calls are audited + budgeted)
    assert spec.reviser is not None and spec.reviser._route_context is ctx

def test_context_is_mandatory():
    # F3: there is no way to build an unaudited/unbudgeted proposal panel.
    with pytest.raises(TypeError):
        build_proposal_review_spec(
            backend=object(), repo_root=Path("."),
            proposer_baseline=IndependenceBaseline(), )  # no route_context

def test_ceiling_matches_the_panel_it_builds():
    assert proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS) == 56  # N=5, R=3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_self_improvement_review_spec.py -q`
Expected: FAIL — `ModuleNotFoundError: ... self_improvement_specs`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/llmxive/convergence/self_improvement_specs.py
"""The self-improvement lane's ``run_convergence`` ReviewSpec builders (FR-019,
Constitution VI). Slice 1B delivers the PROPOSAL review (`self_improvement_proposal`)
with the FR-002 two-attempt reroute wired into every lens and the lane's mandatory
routing context shared by the whole panel AND the reviser.

The PATCH review (`self_improvement_patch`) reuses the same ``LLMReviewer`` mechanism
with ``fallback_profile=None`` (required independence, FAIL CLOSED) and is a later slice.

``run_convergence`` itself is unchanged: independence is wired at reviewer CONSTRUCTION,
before the panel reaches the engine (spec line 283)."""

from __future__ import annotations

from pathlib import Path

from llmxive.convergence.lane_reviser import LaneProposalReviser
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import ReviewSpec
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.route_context import LaneRouteContext

PROPOSAL_STAGE = "self_improvement_proposal"
#: The proposal lens set (Self-improvement ReviewSpec table, spec line 278).
PROPOSAL_LENSES = (
    "worthwhile-improvement", "diagnosis-correctness", "tractability",
    "testability", "blast-radius-sanity",
)
PROPOSAL_MAX_ROUNDS = 3          # table line 281 (the engine default)
#: A proposal the panel does not accept is REJECTED pre-claim (transition table line 245).
PROPOSAL_KICKBACK_STAGE = "rejected"

def build_proposal_review_spec(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,       # REQUIRED (F3) — no unaudited lane panel
    artifact_key: str = "proposal.md",
) -> ReviewSpec:
    reviewers = [
        LLMReviewer(
            lens=lens, stage=PROPOSAL_STAGE, backend=backend, repo_root=repo_root,
            profile="independent_review",       # attempt 1: required family independence
            fallback_profile="deep_review",     # attempt 2 on ModelUnavailable: degrade
            independence_against=proposer_baseline,
            route_context=route_context,
        )
        for lens in PROPOSAL_LENSES
    ]
    reviser = LaneProposalReviser(
        backend=backend, route_context=route_context, artifact_key=artifact_key,
    )
    return ReviewSpec(
        stage=PROPOSAL_STAGE,
        artifacts=[artifact_key],
        reviewers=reviewers,
        reviser=reviser,
        kickback_routing=_kickback_routing(),   # per Step 0(a): every Severity → rejected
        overflow_goal=PROPOSAL_KICKBACK_STAGE,
        advance_stage=None,                     # the lifecycle transition is a later slice
        max_rounds=PROPOSAL_MAX_ROUNDS,
    )
```

(`_kickback_routing()` is the small helper Step 0(a) defines by reading the `Severity` literal and the research builder's convention.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_self_improvement_review_spec.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/self_improvement_specs.py agents/prompts/panels tests/unit/test_self_improvement_review_spec.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T7): self_improvement_proposal ReviewSpec + 5 lens prompts"
```

---

### Task 8: `run_proposal_review` — the lane entry point that fails closed

**Files:**
- Modify: `src/llmxive/convergence/self_improvement_specs.py`
- Test: `tests/unit/test_run_proposal_review.py`

**Interfaces:**
- Consumes: `build_proposal_review_spec` (Task 7); `run_convergence` (`engine.py:393`); `RouteAuditError`, `RouteReplayError` (slice-0 `attempt_hooks`); `LaneCallCeilingExceeded` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class ProposalReviewOutcome`: `result: ConvergenceResult | None`, `failed_closed: bool`, `failure_kind: str` (`""` | `"audit_fatal"` | `"replay"` | `"ceiling"`), `failure_detail: str`.
  - `run_proposal_review(*, backend, repo_root, proposer_baseline, route_context, artifacts, artifact_key="proposal.md", constitution=None, advisory=None) -> ProposalReviewOutcome` — builds the spec and calls `run_convergence(spec, artifacts, constitution=..., advisory=...)`, then owns the lane's **fail-closed** classification:
    - `RouteAuditError` → `failed_closed=True, failure_kind="audit_fatal"`. **Why here:** the engine's `_abort_provenance` (`engine.py:433-448`) catches ONLY `BackendUnavailable`/`TransientBackendError`, so these lane errors would otherwise propagate raw with no provenance. Per FR-033a an audit-abort is a failed logical call — NOT a `ModelUnavailable`, so it never triggers the reroute and never advances a candidate.
    - `RouteReplayError` → `failed_closed=True, failure_kind="replay"`. Per FR-033a's route-replay disposition: never rerouted, never chain-advanced, reservation stays `retained`, reconciled from durable dispatch state — and explicitly **never retried** as a transient error.
    - `LaneCallCeilingExceeded` → `failed_closed=True, failure_kind="ceiling"` (Policy Contract line 313).
    - `BackendUnavailable`/`TransientBackendError` are **not** caught here — the engine already records them via `on_abort` and the run parks to resume, which is the existing clean-abort contract.
  - The Attempt-lifecycle write (`proposal_verified` / `rejected` / `*_failed`) is deliberately NOT performed here — Slice 1A scoped Attempt-failure semantics out. This function reports the outcome; a later slice consumes it.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_run_proposal_review.py
from pathlib import Path

import pytest

from llmxive.model_selection.attempt_hooks import RouteAuditError, RouteReplayError
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.route_context import (
    LaneCallCeilingExceeded, LaneRouteContext, proposal_call_ceiling,
)

class _Sink:
    def record(self, event) -> None: ...
    def claim_dispatch(self, event) -> bool: return True

class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool: return True
    def release(self, reservation_id) -> None: ...
    def mark_retained(self, reservation_id) -> None: ...

def _ctx(tmp_path):
    return LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="lane",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ceiling=proposal_call_ceiling(5, 3),
    )

def _run(tmp_path, monkeypatch, boom):
    from llmxive.convergence import self_improvement_specs as mod

    def _fake_run_convergence(spec, artifacts, **kw):
        raise boom

    monkeypatch.setattr(mod, "run_convergence", _fake_run_convergence)
    return mod.run_proposal_review(
        backend=object(), repo_root=Path("."), proposer_baseline=IndependenceBaseline(),
        route_context=_ctx(tmp_path), artifacts={"proposal.md": "# P"},
    )

def test_audit_fatal_fails_closed(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, RouteAuditError("sink down"))
    assert out.failed_closed and out.failure_kind == "audit_fatal" and out.result is None

def test_replay_fails_closed_and_is_never_retried(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, RouteReplayError("already dispatched"))
    assert out.failed_closed and out.failure_kind == "replay"

def test_ceiling_fails_closed(tmp_path, monkeypatch):
    out = _run(tmp_path, monkeypatch, LaneCallCeilingExceeded("out of calls"))
    assert out.failed_closed and out.failure_kind == "ceiling"

def test_backend_unavailable_is_not_swallowed(tmp_path, monkeypatch):
    # The engine already records + re-raises this clean abort; the lane must NOT convert
    # it into a fail-closed outcome (the run parks and resumes next tick).
    from llmxive.backends.base import BackendUnavailable
    with pytest.raises(BackendUnavailable):
        _run(tmp_path, monkeypatch, BackendUnavailable("breaker open"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_run_proposal_review.py -q`
Expected: FAIL — `AttributeError: module ... has no attribute 'run_proposal_review'`.

- [ ] **Step 3: Write minimal implementation** (append to `self_improvement_specs.py`)

```python
from dataclasses import dataclass

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.types import ConvergenceResult
from llmxive.model_selection.attempt_hooks import RouteAuditError, RouteReplayError
from llmxive.self_improvement.route_context import LaneCallCeilingExceeded

@dataclass(frozen=True)
class ProposalReviewOutcome:
    result: ConvergenceResult | None
    failed_closed: bool
    failure_kind: str      # "" | "audit_fatal" | "replay" | "ceiling"
    failure_detail: str

def run_proposal_review(
    *,
    backend: object,
    repo_root: Path,
    proposer_baseline: IndependenceBaseline,
    route_context: LaneRouteContext,
    artifacts: dict[str, str],
    artifact_key: str = "proposal.md",
    constitution: str | None = None,
    advisory: list[str] | None = None,
) -> ProposalReviewOutcome:
    """Run the proposal panel through the SHARED, UNMODIFIED ``run_convergence`` and own
    the lane's fail-closed classification. The engine's ``_abort_provenance``
    (``engine.py:433-448``) catches only ``BackendUnavailable``/``TransientBackendError``,
    so the three lane-fatal conditions are classified here instead of propagating raw."""
    spec = build_proposal_review_spec(
        backend=backend, repo_root=repo_root, proposer_baseline=proposer_baseline,
        route_context=route_context, artifact_key=artifact_key,
    )
    try:
        result = run_convergence(spec, artifacts, constitution=constitution, advisory=advisory)
    except RouteAuditError as exc:
        # FR-033a: route-fatal. NOT a ModelUnavailable → never reroutes, never advances.
        return ProposalReviewOutcome(None, True, "audit_fatal", str(exc))
    except RouteReplayError as exc:
        # FR-033a route-replay disposition: a failed logical call — reservation stays
        # retained, reconcile from durable dispatch state, NEVER retry as transient.
        return ProposalReviewOutcome(None, True, "replay", str(exc))
    except LaneCallCeilingExceeded as exc:
        return ProposalReviewOutcome(None, True, "ceiling", str(exc))
    return ProposalReviewOutcome(result, False, "", "")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_run_proposal_review.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/llmxive/convergence/self_improvement_specs.py tests/unit/test_run_proposal_review.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-1B T8): run_proposal_review entry point with lane fail-closed classification"
```

---

### Task 9: Integration — the REAL `run_convergence` panel, end to end

**Files:**
- Test: `tests/integration/test_self_improvement_proposal_review.py`

**Interfaces:** none produced (test-only). This is the F11 proof: the production reviewer path — `LLMReviewer` → `chat_with_model_fallback` → `_walker_route` → `route_chat` → the REAL `EventStoreRouteAudit`/`AttemptCreditLedger` — driven by the REAL `run_convergence` engine (including its `ThreadPoolExecutor` panel dispatch), with the reroute exercised.

- [ ] **Step 0 (do first): get the exact panel reply format.** Read `agents/prompts/_shared/panel_review_block.md` and `llm_reviewer.py`'s identify/re-review PARSERS. Craft `ScriptedBackend` replies that the PRODUCTION parsers accept for both `identify` (R1 concerns) and `rereview` (R3 verdicts), plus a `LaneProposalReviser`-shaped ```json reply for R2. **Never weaken a parser to make the test pass** — if a reply does not parse, fix the reply.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_proposal_review.py
"""F11: the REAL LLMReviewer → chat_with_model_fallback → _walker_route → route_chat
path, driven by the REAL run_convergence engine, against the REAL lane audit sink +
Attempt credit ledger. No mock at any layer: a ScriptedBackend supplies model replies,
a real temp git repo backs the lane log, and a real (aged) snapshot drives the reroute.
"""
import subprocess

import pytest

from llmxive.convergence.self_improvement_specs import PROPOSAL_LENSES, PROPOSAL_MAX_ROUNDS, run_proposal_review
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.credit_ledger import AttemptCreditLedger
from llmxive.self_improvement.invocation_identity import build_invocation_identity
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import LaneRouteContext, proposal_call_ceiling

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

@pytest.fixture
def lane(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    cfg = LaneLogConfig()                       # local-only (no remote) for the test
    bootstrap_lane_log(tmp_path, config=cfg)
    clock = lambda: "2026-07-25T00:00:00+00:00"
    sink = EventStoreRouteAudit(repo=tmp_path, problem_id="P1", attempt_id="A1",
                                actor="lane", clock=clock, config=cfg)
    ledger = AttemptCreditLedger(repo=tmp_path, problem_id="P1", attempt_id="A1",
                                 attempt_budget_credits=1000.0, actor="lane", clock=clock, config=cfg)
    ctx = LaneRouteContext(
        repo=tmp_path, problem_id="P1", attempt_id="A1", actor="lane", clock=clock,
        route_audit=sink, reservation_authority=ledger,
        call_ceiling=proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS), config=cfg,
    )
    return tmp_path, ctx

def test_full_proposal_panel_audits_every_call_and_records_the_reroute(lane, monkeypatch):
    repo, ctx = lane
    # A snapshot fresh enough for deep_review (max_catalog_age_s=3600) but TOO STALE for
    # independent_review (900 + require_fresh_snapshot) → attempt 1 raises ModelUnavailable
    # and every lens reroutes. Reuse the model_selection snapshot builders (see
    # tests/unit/test_model_selection_route.py::_snapshot) and inject via the snapshot seam.
    snap = _aged_snapshot(age_s=1800.0)          # helper written in Step 0
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)
    backend = _ScriptedPanelBackend()             # Step 0: production-parseable replies

    outcome = run_proposal_review(
        backend=backend, repo_root=_repo_root_with_prompts(),  # the real repo prompts
        proposer_baseline=IndependenceBaseline(families=frozenset({"qwen3.5"})),
        route_context=ctx, artifacts={"proposal.md": "# Proposal\n\nNarrow the retry loop."},
    )

    assert not outcome.failed_closed and outcome.result is not None

    events = read(repo, "P1")
    kinds = [e.event_type for e in events]
    # every lens rerouted → one explicit record per lens, and BOTH legs are audited
    assert kinds.count("ReviewRerouted") == len(PROPOSAL_LENSES)
    assert "SelectionFailure" in kinds and "ChainResolved" in kinds
    assert "DispatchCompleted" in kinds

    # the fallback leg named by an explicit reroute record yields a degraded identity
    rr = next(e for e in events if e.event_type == "ReviewRerouted")
    ii = build_invocation_identity(events, route_id=rr.payload["fallback_route_id"])
    assert ii is not None and ii.route_outcome == "independence_degraded"
    assert ii.degradation.primary_profile == "independent_review"
    assert ii.serving_endpoint and ii.vendor        # full selection provenance present

    # the ceiling accounted BOTH legs of every reviewer op plus the reviser's calls
    assert ctx.calls_used() >= 2 * len(PROPOSAL_LENSES)
    assert ctx.calls_used() <= ctx.call_ceiling

def test_reviser_calls_are_audited_too(lane, monkeypatch):
    # F3: the reviser is a lane LLM call — its route must appear in the SAME audit
    # stream, with its spend on the SAME Attempt. Drive a run whose R1 raises a concern
    # per lens so R2 (the reviser) actually executes.
    repo, ctx = lane
    snap = _aged_snapshot(age_s=1800.0)
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)
    backend = _ScriptedPanelBackend(raise_concerns=True)   # R1 concerns → R2 runs → R3 passes

    outcome = run_proposal_review(
        backend=backend, repo_root=_repo_root_with_prompts(),
        proposer_baseline=IndependenceBaseline(families=frozenset({"qwen3.5"})),
        route_context=ctx, artifacts={"proposal.md": "# Proposal\n\nNarrow the retry loop."},
    )
    assert not outcome.failed_closed

    events = read(repo, "P1")
    audited_routes = {e.payload["route_id"] for e in events if e.event_type == "ChainResolved"}
    reroute_legs = set()
    for e in events:
        if e.event_type == "ReviewRerouted":
            reroute_legs.add(e.payload["primary_route_id"])
            reroute_legs.add(e.payload["fallback_route_id"])
    # At least one audited route belongs to NO reviewer reroute pair — that is the
    # reviser's own routed call, proving it was audited like every other lane call.
    assert audited_routes - reroute_legs, "the reviser's route was not audited"
    # and it was charged against the same Attempt ceiling as the panel
    assert ctx.calls_used() > 2 * len(PROPOSAL_LENSES)
```

**Note for the implementer:** `_ScriptedPanelBackend(raise_concerns: bool = False)`, `_aged_snapshot(age_s)`, and `_repo_root_with_prompts()` are the three helpers Step 0 produces. Reuse the existing real doubles (`ScriptedBackend` from `tests/integration/test_model_selection_execute.py`, the `_snapshot` builder from `tests/unit/test_model_selection_route.py`); `_repo_root_with_prompts()` returns the actual repo root (`llmxive.config.repo_root()`) so the REAL Task-7 prompts are loaded. `_ScriptedPanelBackend` must return: production-parseable R1 identify replies (zero concerns when `raise_concerns=False`, one concern per lens when `True`), a `LaneProposalReviser`-shaped ```json reply for R2, and passing R3 verdicts.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_proposal_review.py -q`
Expected: FAIL until the helpers exist and Tasks 1-8 are complete.

- [ ] **Step 3: Wire the helpers + make it pass** (no production change expected — this test exercises Tasks 1-8 together; if it reveals a wiring defect, fix the CODE, never the assertions).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_proposal_review.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_proposal_review.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1B T9): real run_convergence proposal panel — audited calls + recorded reroute"
```

---

### Task 10: Integration — concurrent panel reviewers compete for the last Attempt credits

**Files:**
- Test: `tests/integration/test_self_improvement_proposal_credits.py`

**Interfaces:** none produced (test-only). This is the F2 proof the maintainer required: "an integration test that runs the convergence panel ITSELF with concurrent paid reviewer operations competing for the final Attempt credits. A direct `execute()` test is necessary but not sufficient."

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_self_improvement_proposal_credits.py
"""F2: the Attempt budget binds through the PANEL, not just through a direct execute()
call. The engine dispatches the 5 lenses through a real ThreadPoolExecutor
(engine.py:85-133, cap 8), all sharing ONE AttemptCreditLedger, so this exercises the
genuine concurrent-reservation path with paid opt-in ON."""
import subprocess

import pytest

from llmxive.convergence.self_improvement_specs import PROPOSAL_LENSES, PROPOSAL_MAX_ROUNDS, run_proposal_review
from llmxive.model_selection.types import IndependenceBaseline
from llmxive.self_improvement.audit_sink import EventStoreRouteAudit
from llmxive.self_improvement.credit_ledger import (
    AttemptCreditLedger, counting_total, project_reservations,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import LaneRouteContext, proposal_call_ceiling

def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path

def test_concurrent_panel_reviewers_never_exceed_the_attempt_budget(repo, monkeypatch):
    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    # A budget that admits only SOME of the 5 concurrent reviewer reservations.
    budget = 3.0 * 2.5                      # room for ~3 of 5 worst-case envelopes
    clock = lambda: "2026-07-25T00:00:00+00:00"
    cfg = LaneLogConfig()
    ledger = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                                 attempt_budget_credits=budget, actor="lane", clock=clock, config=cfg)
    sink = EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id="A1",
                                actor="lane", clock=clock, config=cfg)
    ctx = LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="lane", clock=clock,
        route_audit=sink, reservation_authority=ledger,
        call_ceiling=proposal_call_ceiling(len(PROPOSAL_LENSES), PROPOSAL_MAX_ROUNDS), config=cfg,
    )
    # A PAID-only chain + a scripted backend, so every lens must reserve before dispatch.
    snap = _paid_only_snapshot()             # Step 0 helper (mirrors the paid fixtures)
    monkeypatch.setattr("llmxive.model_selection.route._acquire_snapshot", lambda: snap)

    run_proposal_review(
        backend=_ScriptedPanelBackend(), repo_root=_repo_root_with_prompts(),
        proposer_baseline=IndependenceBaseline(), route_context=ctx,
        artifacts={"proposal.md": "# Proposal"},
    )

    # THE invariant (US1 scenario 5): the sum of reserved envelopes never exceeds the cap,
    # no matter how the 5 concurrent reviewers interleaved.
    reservations = project_reservations(read(repo, "P1"), "A1")
    assert counting_total(reservations) <= budget
    # and the reservations that DID open are all accounted (no silent unpriced dispatch)
    assert reservations, "expected at least one paid reservation to have opened"
    for r in reservations.values():
        assert r.state in {"open", "retained", "reconciled", "released"}
```

**Note for the implementer:** `_paid_only_snapshot` mirrors the paid-candidate fixtures in `tests/integration/test_model_selection_execute.py` (a chain whose candidates are NOT free, with a `live` credit snapshot so the C6 guard passes). The reviewers whose reservation is refused skip/advance and ultimately surface as a clean abort — assert the BUDGET invariant, not a particular per-lens outcome, since the interleaving is genuinely nondeterministic.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_self_improvement_proposal_credits.py -q`
Expected: FAIL until the helpers exist and Tasks 1-8 are complete.

- [ ] **Step 3: Wire the helpers + make it pass** (fix the CODE if the invariant is violated — never relax the assertion).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_self_improvement_proposal_credits.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_self_improvement_proposal_credits.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(025 slice-1B T10): concurrent panel reviewers never exceed the Attempt budget"
```

---

## Final verification (before the whole-branch review)

- [ ] Package exports (`src/llmxive/self_improvement/__init__.py`): add `LaneRouteContext`, `LaneCallCeilingExceeded`, `proposal_call_ceiling`, `InvocationIdentity`, `IndependenceDegraded`, `build_invocation_identity`. Test they import.
- [ ] `ruff check` clean on every touched file.
- [ ] Full non-slow suite green: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → 0 failed (network-restricted-sandbox artifacts itemized).
- [ ] `enforcement.py` guard passes: no model-id literal in lane code (`pytest tests/unit -k enforcement -q`).
- [ ] Behavior preservation spot-check: `pytest tests/unit -k "router or llm_reviewer or convergence" -q` → the research/paper path is unchanged.
- [ ] Prompt-eval gate: `agents/prompts/**` changed, so the promptfoo eval (`.github/workflows/prompt-eval.yml`) applies to the 5 new lens prompts — confirm they follow the house structure Step 0(b) verified.
- [ ] Commit discipline honored on every task; **nothing pushed**.

## Requirement traceability

| Source | Requirement | Task |
|-|-|-|
| Round-1 review F2 | `reservation_authority` threaded to reviewers AND reviser; panel-level concurrent-credit test | T2, T3, T4, T5, T7, **T10** |
| Round-1 review F3 | Mandatory audit (no `route_audit=None` default); reviser covered | T2 (required fields), T5, T7 (required param) |
| Round-1 review F10 | EXPLICIT reroute/degradation event; complete `InvocationIdentity` (endpoint/vendor/provenance) | T1, T2 (`record_reroute`), T4, T6 |
| Round-1 review F11 | Real production reviewer path through `run_convergence` | **T9** |
| FR-002 | Two-attempt reroute, `independent_review` → `deep_review`, degrade-never-fail-closed, no new profile | T4, T7 |
| FR-002 (patch binding) | Same mechanism, `fallback_profile=None` → fail closed | T4 (covered by test; the patch ReviewSpec is a later slice) |
| FR-033a | Route-fatal audit abort; route-replay disposition | T8 |
| Policy Contract line 313 | Stage-specific ceiling `4N + R·(2N+2)`; reviser is ONE call | T2, T5, T9 |
| ReviewSpec table lines 273-283 | Stage, lens set, reviser, profiles, independence binding, `max_rounds=3` | T7 |
| Key Entities line 227 | `InvocationIdentity` sourced from the audit sink | T6 |
| SC-008 | All lane calls via `route_chat`; no model-id literals | T3, T4, T5 + final verification |
