# Self-Improvement Lane — Slice 0: `route_chat` 026 Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the delivered 026 `route_chat`→`execute` chokepoint with the two threaded hooks and one field that spec 025 (`specs/025-self-improvement-lane/spec.md`, rev13) depends on — `reservation_authority` (Attempt-budget enforcement), `route_audit` (mandatory durable audit sink), and `ExecutionResult.reservation_id` — WITHOUT changing any existing behavior when those hooks are absent.

**Architecture:** All work is in the protected `src/llmxive/model_selection/**` layer. This is **trusted prerequisite work** (done by us, not by the self-improvement lane, which may never touch this surface — FR-013). The hooks are optional params defaulting to `None`; when both are `None`, `route_chat`/`execute` behave byte-for-byte as today. The lane supplies the real implementations (`AttemptCreditLedger` as the `ReservationAuthority`, an event-sourced `RouteAudit` sink) in slice 3+; slice 0 defines the **protocols** and wires the **call sites**, exercised by real in-test implementations.

**Tech Stack:** Python ≥ 3.11; `pytest`; the package is `llmxive.model_selection` (import root: `from llmxive.model_selection import …`). No new third-party deps.

## Global Constraints

- **Behavior-preserving default (the load-bearing invariant):** with `reservation_authority=None` AND `route_audit=None`, `route_chat` and `execute` MUST behave exactly as today. The full non-slow suite (`pytest tests/unit tests/contract tests/integration -m "not slow"`, currently **7123 passed / 17 skipped / 0 failed**) MUST stay green after every task.
- **No model-id literals outside the canonical layer** — `model_selection/enforcement.py` statically enforces this; do not introduce any pin. (Slice 0 adds no model ids.)
- **Real tests, no mocks (Constitution III / user rule):** test doubles that *implement a Protocol with real logic* (an in-memory budget counter, an in-memory event list) are real minimal implementations — the same injection-seam pattern 026 already uses for `backend_factory`/`credit_observer`/`balance_fetch`. Do NOT use `unittest.mock`.
- **Keep the autouse `_offline_model_selection_snapshot` fixture** (offline snapshot stub) — do not remove or bypass it.
- **Commit each task** with `PRE_COMMIT_ALLOW_NO_CONFIG=1` and the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; after committing, verify `HEAD` moved (`git log --oneline -1`).
- **Do NOT push.** The `025-self-improvement-lane` branch rebases onto `origin/main` only at PR time (local `main` lags ~785 commits).
- Spec cross-refs live in `specs/025-self-improvement-lane/spec.md`: FR-033(a)–(e) (lines 209–221), FR-002 (147–151), the `route_audit`/`reservation_authority` contract (212), entities (223–229).

---

## Test Harness Reuse (confirmed real helpers — do NOT invent fixtures)

Slice 0's tests REUSE the delivered 026 test harness. Place each test in the file whose helpers it needs (all confirmed to exist):

- **Pure contract tests** (no chain/backend/ledger) → NEW file `tests/unit/test_model_selection_attempt_hooks.py`: the `ExecutionResult.reservation_id` field (T1), the hook types (T2), the exports (T6). Define the REAL in-test hook implementations here — `_Budget` (a `ReservationAuthority`), `_Recorder` / `_FailingRecorder` (a `RouteAudit`). These are real minimal implementations, not mocks.
- **Free-path `execute` tests** (T4 outbox lifecycle, route-fatal pre-dispatch) → add to `tests/unit/test_model_selection_execute.py`, reusing its module-level helpers: `_free_candidate(model_id)`, `_chain(*candidates, credit_source="live", budget=None)`, `class ScriptedBackend({model_id: "ok"|Exception})` + `_factory(be)` (the FR-015 backend seam; empty script `{}` = all-ok), and `MSG = [ChatMessage(role="user", content="hello")]`. Import `_Recorder`/`_FailingRecorder` from the T2 module (or duplicate the ~10-line impls).
- **Paid-path `execute` tests** (T3 authority admit/deny, T4 post-dispatch retained) → add to `tests/integration/test_model_selection_execute.py`, reusing its real git-ledger harness: the `repo` fixture (a real `git init` tmp ledger), `_paid_chain(*, model_id=CLAUDE, worst_case=2.5, credit_source="live")`, the injected fresh-credit seams `_observer(spend=100.0, cap=1500.0)` (→ `credit_observer=`) and `_balance(spend=100.0, max_budget=2000.0)` (→ `balance_fetch=`), `LOCAL_CFG = LedgerConfig(remote=None)`, `MSG`, and a fake ok backend via `backend_factory`. Import `_Budget`/`_FailingRecorder` from the T2 module.
- **`route_chat` tests** (T5 `ChainResolved`, `SelectionFailure`) → add to `tests/unit/test_model_selection_route.py`, reusing its snapshot builder (same `_snapshot(model_ids=…)` pattern as `tests/unit/test_model_selection_select.py:51`). An "eligible" snapshot = the default `_snapshot()`; a "no-eligible" snapshot (forces `ModelUnavailable`) = a `_snapshot(model_ids=[…])` restricted so `select` finds nothing, exactly as `test_model_selection_select.py` does.

The task bodies below sometimes use shorthand fixture names (`paid_chain_and_repo`, `free_chain_and_messages`, `offline_snapshot`, `empty_snapshot`); resolve each to the real helpers above. Corrected inline code is given for T3/T4/T5's key tests.

---

## Slice Roadmap (context — only Slice 0 is detailed below)

| Slice | Scope | Depends on |
|-|-|-|
| **0 (this plan)** | `route_chat`/`execute` hooks: `reservation_authority`, `route_audit`, `ExecutionResult.reservation_id` (protected 026 layer) | 026 (done) |
| 1 | Store + append-only events + optimistic concurrency + singleton `LaneCoordinator`; error mining; issue ranking/pagination; proposer + deterministic pre-gates + proposal `run_convergence` (two-attempt reroute wiring in `convergence/`); `AttemptCreditLedger` + `RouteAudit` sink implementations (US1) | 0 |
| 2 | Coordinator CAS claim transaction, reconciliation, label/comment (US2) | 1 |
| 3 | Implementation + candidate-publisher domains; hardened container; diff policy + budgets; `PROTECTED_MODEL_EXECUTION_SURFACE`; `unsupported_scope` (US3) | 2 |
| 4 | Trusted paired controller + immutable workload + `EvaluationContract`; allowlisted `base_reproducer`; check-verification; App-token merge to canary (US4) | 3 |
| 5 | Concurrent monitoring; corroborated attribution; ancestry; auto-revert; breakers (US5) | 4 |
| 6 | Live-main promotion gates + flag + App/branch-protection (US6) | 5 |

Each subsequent slice gets its own plan, written just before it executes. This document covers **Slice 0 only**.

---

## File Structure (Slice 0)

- **Create** `src/llmxive/model_selection/attempt_hooks.py` — the `ReservationAuthority` Protocol, the `RouteAudit` Protocol, the frozen `RouteAuditEvent` dataclasses, and `RouteAuditError`. One file, one responsibility: the typed hook contracts the lane implements and the chokepoint calls.
- **Modify** `src/llmxive/model_selection/execute.py` — add `reservation_id` to `ExecutionResult`; thread `reservation_authority` through `_open_paid_reservation`; thread `route_audit` through the candidate loop (outbox lifecycle + route-fatal pre-dispatch semantics).
- **Modify** `src/llmxive/model_selection/route.py` — add the two params to `route_chat`; emit `SelectionFailure`/`ChainResolved` audit events around `select`; pass both hooks to `execute`.
- **Modify** `src/llmxive/model_selection/__init__.py` — export the new public names.
- **Create** `tests/unit/test_model_selection_attempt_hooks.py` — the hook-contract + wiring tests, using real in-test implementations.

---

### Task 1: `ExecutionResult.reservation_id`

Add the winner's reservation id to the execution result (FR-033a: "`ExecutionResult` additionally exposes the winner's `reservation_id`"). Additive, default `None` → free-only chains and existing callers are unaffected.

**Files:**
- Modify: `src/llmxive/model_selection/execute.py:82-91` (the `ExecutionResult` dataclass) and `:305-310` (its one construction site)
- Test: `tests/unit/test_model_selection_attempt_hooks.py`

**Interfaces:**
- Produces: `ExecutionResult(response, model_ref, reserved_credits, notes, reservation_id: str | None = None)` — the last field is the ledger reservation id of the winning candidate, or `None` for a free winner.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_model_selection_attempt_hooks.py
from llmxive.model_selection.execute import ExecutionResult
from llmxive.model_selection.types import ModelRef


def _ref() -> ModelRef:
    return ModelRef(backend="dartmouth", serving_endpoint="dartmouth",
                    model_id="qwen.qwen3.5-122b", model_family="qwen3.5", vendor="qwen")


def test_execution_result_carries_reservation_id():
    r = ExecutionResult(response=None, model_ref=_ref(), reserved_credits=0.0,
                        notes=(), reservation_id="qwen-qwen3-5-122b-abc123")
    assert r.reservation_id == "qwen-qwen3-5-122b-abc123"


def test_execution_result_reservation_id_defaults_none():
    r = ExecutionResult(response=None, model_ref=_ref(), reserved_credits=0.0, notes=())
    assert r.reservation_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'reservation_id'`.

- [ ] **Step 3: Add the field and populate it**

In `src/llmxive/model_selection/execute.py`, add the field to `ExecutionResult` (after `notes`):

```python
@dataclass(frozen=True)
class ExecutionResult:
    """The outcome of a successful :func:`execute`: the provider ``response``, the
    ``model_ref`` that produced it, the credits ``reserved`` for it (0 for free),
    per-candidate ``notes`` (skips / advances that preceded success), and the
    winning candidate's ledger ``reservation_id`` (``None`` for a free winner —
    FR-033a: the lane attributes settled Attempt cost by this id)."""

    response: ChatResponse
    model_ref: ModelRef
    reserved_credits: float
    notes: tuple[str, ...]
    reservation_id: str | None = None
```

At the success return (`execute.py:305`), pass it through:

```python
            return ExecutionResult(
                response=response,
                model_ref=ref,
                reserved_credits=reserved_credits,
                notes=tuple(notes),
                reservation_id=reservation_id,
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Regression — the additive field breaks nothing**

Run: `pytest tests/unit/test_model_selection_execute.py tests/unit/test_model_selection_route.py -q`
Expected: PASS (no failures). If a test constructs `ExecutionResult` positionally past `notes`, it will still pass because the new field is last with a default.

- [ ] **Step 6: Commit**

```bash
git add src/llmxive/model_selection/execute.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T1): ExecutionResult.reservation_id (FR-033a)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 2: The hook contracts — `attempt_hooks.py`

Define the two Protocols the lane implements, the audit event types (the outbox lifecycle), and the route-fatal error. Pure type/interface module: no I/O, no networked imports, so it is safe to import eagerly from the package root.

**Files:**
- Create: `src/llmxive/model_selection/attempt_hooks.py`
- Test: `tests/unit/test_model_selection_attempt_hooks.py`

**Interfaces:**
- Produces:
  - `RouteAuditError(RuntimeError)` — raised when a mandatory `route_audit.record()` fails; route-fatal pre-dispatch.
  - `ReservationAuthority` Protocol: `reserve(credits: float, *, reservation_id: str, call_id: str) -> bool`; `release(reservation_id: str) -> None`; `mark_retained(reservation_id: str) -> None`.
  - `RouteAudit` Protocol: `record(event: RouteAuditEvent) -> None`.
  - `RouteAuditEvent` union of frozen dataclasses: `ChainResolved`, `SelectionFailure`, `ReservationOpened`, `DispatchStarted`, `DispatchCompleted`, `CandidateOutcome`. (`DispatchUnknown` is produced by the lane's *reconciler* — slice 3+ — from a durable un-completed `DispatchStarted`, so it is defined here but never emitted by `execute`.)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/test_model_selection_attempt_hooks.py
from llmxive.model_selection.attempt_hooks import (
    ChainResolved, DispatchStarted, ReservationAuthority, RouteAudit,
    RouteAuditError, SelectionFailure,
)


class _Budget:
    """A REAL in-memory ReservationAuthority: an Attempt budget counter."""
    def __init__(self, cap: float):
        self.cap = cap
        self.open: dict[str, float] = {}
        self.retained: set[str] = set()
        self.released: set[str] = set()

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        if sum(self.open.values()) + credits > self.cap:
            return False
        self.open[reservation_id] = credits
        return True

    def release(self, reservation_id: str) -> None:
        self.open.pop(reservation_id, None)
        self.released.add(reservation_id)

    def mark_retained(self, reservation_id: str) -> None:
        self.retained.add(reservation_id)


class _Recorder:
    """A REAL in-memory RouteAudit sink."""
    def __init__(self):
        self.events: list = []

    def record(self, event) -> None:
        self.events.append(event)


def test_reservation_authority_is_structural():
    b = _Budget(10.0)
    assert isinstance(b, ReservationAuthority)
    assert b.reserve(4.0, reservation_id="r1", call_id="c1") is True
    assert b.reserve(7.0, reservation_id="r2", call_id="c1") is False  # over cap


def test_route_audit_is_structural_and_records_events():
    rec = _Recorder()
    assert isinstance(rec, RouteAudit)
    rec.record(ChainResolved(snapshot_digest="d", selection_policy_version=1,
                             resolved_at="t", explanation=(), candidate_model_ids=("m",)))
    rec.record(DispatchStarted(model_id="m", reservation_id=None))
    assert len(rec.events) == 2


def test_route_audit_error_is_runtime_error():
    assert issubclass(RouteAuditError, RuntimeError)
    assert not issubclass(RouteAuditError, ValueError)


def test_selection_failure_carries_structured_reason():
    ev = SelectionFailure(exception_type="ModelUnavailable", message="none eligible",
                          requirement_digest="rq", snapshot_provenance="catalog=live")
    assert ev.exception_type == "ModelUnavailable"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'llmxive.model_selection.attempt_hooks'`.

- [ ] **Step 3: Create the module**

```python
# src/llmxive/model_selection/attempt_hooks.py
"""Typed hook contracts for the spec-025 self-improvement lane (026 follow-up).

The lane cannot enforce a per-Attempt credit budget or capture routing provenance
from outside ``route_chat`` (the candidate + its ``worst_case_credits`` are unknown
until ``select`` runs, and ``route_chat`` returns only a ``ChatResponse``). So the
chokepoint accepts two OPTIONAL hooks the lane injects:

- ``ReservationAuthority`` — an ENFORCEMENT gate consulted before each paid dispatch;
  it can DENY (skip the candidate). Its ``reserve`` MUST NOT raise for an ordinary
  budget denial (it returns ``False``); an infrastructure failure may raise and is
  surfaced.
- ``RouteAudit`` — a MANDATORY, SYNCHRONOUS, durable audit sink (NOT best-effort
  telemetry). It follows an OUTBOX lifecycle: ``ChainResolved`` → ``ReservationOpened``
  → ``DispatchStarted`` (all durable BEFORE the backend call) → ``DispatchCompleted``.
  A ``record`` exception is never swallowed: pre-dispatch it is route-fatal
  (``RouteAuditError``), post-dispatch the call fails closed with the reservation
  preserved. ``DispatchUnknown`` is produced by the lane's reconciler from a durable
  un-completed ``DispatchStarted`` — the chokepoint never emits it.

This module is pure types (no I/O, no networked imports), so it is safe to import
eagerly from the package root — unlike ``snapshot``/``route``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class RouteAuditError(RuntimeError):
    """A mandatory ``RouteAudit.record`` call failed. Route-fatal when raised
    pre-dispatch: it ABORTS the logical route call and NEVER advances to another
    candidate (an audit outage must not silently change which model executes).
    Distinct from ``ModelUnavailable`` (nothing eligible) and ``ChainExhausted``
    (the chain ran, none succeeded), so it does not trigger the proposal reroute."""


@runtime_checkable
class ReservationAuthority(Protocol):
    """An Attempt-scoped budget gate (FR-033). Injected by the lane; the
    model-selection layer only CALLS it, never constructs it."""

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        """Atomically reserve ``credits`` (the worst-case × retries envelope)
        against the Attempt budget. Return ``True`` if admitted, ``False`` if it
        would exceed the budget (the candidate is skipped/advanced). MUST NOT raise
        for an ordinary budget denial."""

    def release(self, reservation_id: str) -> None:
        """Release a reservation that definitively did NOT dispatch (``open →
        released`` — e.g. the 026 daily reserve failed after this one opened, or a
        pre-dispatch audit failure aborted the route)."""

    def mark_retained(self, reservation_id: str) -> None:
        """Mark a DISPATCHED reservation reconciliation-pending (``open →
        retained``); the lane's reconciler later moves it to ``reconciled``."""


@dataclass(frozen=True)
class ChainResolved:
    """Emitted once after ``select`` succeeds, before any dispatch."""

    snapshot_digest: str
    selection_policy_version: int
    resolved_at: str
    explanation: tuple[str, ...]
    candidate_model_ids: tuple[str, ...]


@dataclass(frozen=True)
class SelectionFailure:
    """Emitted when ``select`` raises ``ModelUnavailable`` (so the failed first leg
    of the proposal reroute is auditable). Carries the KNOWN raw failure only — no
    causal claim (FR-002/F3)."""

    exception_type: str
    message: str
    requirement_digest: str
    snapshot_provenance: str


@dataclass(frozen=True)
class ReservationOpened:
    """Emitted once per paid candidate whose Attempt + 026 reservations both opened."""

    reservation_id: str
    model_id: str
    reserved_credits: float


@dataclass(frozen=True)
class DispatchStarted:
    """Emitted (durably) immediately BEFORE the backend call for a candidate."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class DispatchCompleted:
    """Emitted immediately AFTER a successful backend call for a candidate."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class DispatchUnknown:
    """NOT emitted by ``execute``. The lane's reconciler produces this from a
    durable ``DispatchStarted`` with no matching ``DispatchCompleted`` (a crash
    between). Defined here so the lane and the chokepoint share one event vocabulary."""

    model_id: str
    reservation_id: str | None


@dataclass(frozen=True)
class CandidateOutcome:
    """Emitted once per candidate terminal disposition."""

    model_id: str
    outcome: str  # "success" | "skip" | "advance" | "abort"
    reason: str


RouteAuditEvent = (
    ChainResolved
    | SelectionFailure
    | ReservationOpened
    | DispatchStarted
    | DispatchCompleted
    | DispatchUnknown
    | CandidateOutcome
)


@runtime_checkable
class RouteAudit(Protocol):
    """A mandatory, synchronous, durable audit sink (FR-033a). ``record`` MUST make
    the event durable before returning; raising is never swallowed (see
    ``RouteAuditError``)."""

    def record(self, event: RouteAuditEvent) -> None: ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -q`
Expected: PASS (all tests from Task 1 + Task 2).

- [ ] **Step 5: Lint the new file**

Run: `ruff check src/llmxive/model_selection/attempt_hooks.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/llmxive/model_selection/attempt_hooks.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T2): ReservationAuthority + RouteAudit hook contracts

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 3: Thread `reservation_authority` through `execute`

Enforce the Attempt budget BEFORE the 026 daily reserve, with the FR-033(b) ordering and rollback. Consulted inside `_open_paid_reservation`; `execute` passes it through. Default `None` → no-op.

**Files:**
- Modify: `src/llmxive/model_selection/execute.py` — `_open_paid_reservation` (`:119-195`), `execute` signature (`:198-211`) + its call to `_open_paid_reservation` (`:272-277`) + the `finally` settle block (`:317-325`)
- Test: `tests/unit/test_model_selection_attempt_hooks.py`

**Interfaces:**
- Consumes: `ReservationAuthority` (Task 2).
- Produces: `execute(..., reservation_authority: ReservationAuthority | None = None)`. Ordering per paid candidate: twice-checked 026 guard → `authority.reserve` (skip on `False`) → 026 daily reserve (on `LedgerError`, `authority.release` + skip) → dispatch. A dispatched paid candidate's reservation is `mark_retained` in `finally` (matching the 026 `settle→settling`); a never-dispatched one is `release`d.

- [ ] **Step 1: Write the failing tests**

Add these to `tests/integration/test_model_selection_execute.py` (its real git-ledger `repo` fixture + `_paid_chain`/`_observer`/`_balance`/`LOCAL_CFG`/`MSG` are already in scope). Import `_Budget` from the T2 unit module, and add a tiny ok-backend factory. `ChainExhausted` is already imported there.

```python
# in tests/integration/test_model_selection_execute.py
from tests.unit.test_model_selection_attempt_hooks import _Budget  # the real in-memory authority


def _ok_factory():
    class _OK:
        def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
            return ChatResponse(text=f"ok:{model}", model=model or "m", backend="scripted")
    return lambda name: _OK()


def test_reservation_authority_denial_skips_paid_candidate(repo):
    budget = _Budget(0.0)  # cap 0 → every Attempt reserve is refused
    with pytest.raises(ChainExhausted):  # the only candidate was skipped
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget)
    assert budget.open == {}          # released/never-held: nothing reserved
    assert budget.retained == set()   # never dispatched


def test_reservation_authority_admits_within_budget(repo):
    budget = _Budget(10_000.0)  # ample
    result = execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                     credit_observer=_observer(), balance_fetch=_balance(),
                     reservation_authority=budget)
    assert result.reservation_id is not None
    assert result.reservation_id in budget.retained  # dispatched → retained (not released)


def test_reservation_authority_none_is_behavior_preserving(repo):
    # No authority → identical to today's paid path (026 reserve only).
    result = execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                     credit_observer=_observer(), balance_fetch=_balance())
    assert result.reservation_id is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/integration/test_model_selection_execute.py -k reservation_authority -q`
Expected: FAIL — `execute() got an unexpected keyword argument 'reservation_authority'`.

- [ ] **Step 3: Thread the authority into `_open_paid_reservation`**

Add the param and move `rid` computation up so the authority and the 026 reserve share it. Replace the reserve section (`execute.py:174-195`) of `_open_paid_reservation`:

```python
def _open_paid_reservation(
    candidate: Candidate,
    chain: ModelChain,
    *,
    options: ExecutionOptions,
    retries: int,
    ledger_repo: Path | None,
    ledger_config: LedgerConfig | None,
    credit_observer: Callable[[], CreditObservation] | None,
    balance_fetch: Callable[[], object] | None,
    now: datetime,
    call_id: str,
    reservation_authority: "ReservationAuthority | None" = None,
) -> tuple[str | None, float, str | None]:
    # ... UNCHANGED through the paid_call_allowed twice-check ...
    if not allowed:
        return None, 0.0, f"paid {ref.model_id!r} skipped: {reason}"

    rid = _sanitize_reservation_id(ref.model_id, call_id)

    # Attempt-budget authority (FR-033b step ii): reserve against the Attempt budget
    # BEFORE the 026 daily reserve. A False = would exceed attempt_budget_credits →
    # skip the candidate (advance); it is NOT an error and opens no 026 reservation.
    if reservation_authority is not None:
        if not reservation_authority.reserve(reserve_credits, reservation_id=rid, call_id=call_id):
            return None, 0.0, (
                f"paid {ref.model_id!r} skipped: Attempt budget exhausted "
                "(reservation_authority refused)"
            )

    lease_expires = now + timedelta(seconds=lease_duration_for(options.deadline_s))
    try:
        reserve(
            ledger_repo,
            reservation_id=rid,
            worst_case_credits=reserve_credits,
            model=ref.model_id,
            credit_observer=observer,
            lease_expires_at=lease_expires,
            now=now,
            config=ledger_config,
        )
    except LedgerError as exc:
        # 026 reserve refused/errored AFTER the Attempt reserve opened → release it
        # (FR-033b: "Attempt reserved but the 026 reserve is refused/errors → release
        # the Attempt reservation, skip candidate"). open → released.
        if reservation_authority is not None:
            reservation_authority.release(rid)
        return None, 0.0, f"paid {ref.model_id!r} skipped: could not reserve ({type(exc).__name__}: {exc})"
    return rid, reserve_credits, None
```

Add the forward-ref import at the top of `execute.py` (function-local is unnecessary — `attempt_hooks` is pure types):

```python
from llmxive.model_selection.attempt_hooks import ReservationAuthority
```

- [ ] **Step 4: Thread it through `execute` and the `finally` block**

Add the param to `execute` (`:198-211`), pass it to `_open_paid_reservation` (`:272-277`), and in the `finally` (`:317-325`) mark a dispatched paid reservation `retained`:

```python
def execute(
    chain: ModelChain,
    messages: Iterable[ChatMessage],
    *,
    options: ExecutionOptions,
    backend_factory: Callable[[str], BaseBackend] = make_backend,
    retries: int = 3,
    ledger_repo: Path | None = None,
    ledger_config: LedgerConfig | None = None,
    credit_observer: Callable[[], CreditObservation] | None = None,
    balance_fetch: Callable[[], object] | None = None,
    now: datetime | None = None,
    call_id: str | None = None,
    reservation_authority: ReservationAuthority | None = None,
) -> ExecutionResult:
```

At the call site:

```python
            reservation_id, reserved_credits, skip = _open_paid_reservation(
                candidate, chain, options=options, retries=retries,
                ledger_repo=ledger_repo, ledger_config=ledger_config,
                credit_observer=credit_observer, balance_fetch=balance_fetch,
                now=now, call_id=call_id, reservation_authority=reservation_authority,
            )
```

In the `finally`, after the 026 settle, mark the Attempt hold retained (it dispatched — `open → retained`):

```python
        finally:
            if reservation_id is not None:
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:
                    logger.warning("execute: settle(%s) failed: %s", reservation_id, exc)
                if reservation_authority is not None:
                    # Dispatched (success OR advance) → reconciliation-pending, never released.
                    reservation_authority.mark_retained(reservation_id)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/integration/test_model_selection_execute.py -k reservation_authority -q`
Expected: PASS (3 passed).

- [ ] **Step 6: Regression — the paid path is unchanged with no authority**

Run: `pytest tests/unit/test_model_selection_execute.py -q`
Expected: PASS (no failures) — the `None` default preserves today's behavior.

- [ ] **Step 7: Commit**

```bash
git add src/llmxive/model_selection/execute.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T3): thread reservation_authority through execute (FR-033b)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 4: Thread `route_audit` through `execute` (outbox + route-fatal)

Emit the per-candidate outbox events, with the F1 route-fatal pre-dispatch rule and the F2 honest post-dispatch guarantee. Default `None` → no audit calls at all.

**Files:**
- Modify: `src/llmxive/model_selection/execute.py` — `execute` signature + candidate loop (`:259-330`)
- Test: `tests/unit/test_model_selection_attempt_hooks.py`

**Interfaces:**
- Consumes: `RouteAudit`, the event dataclasses, `RouteAuditError` (Task 2).
- Produces: `execute(..., route_audit: RouteAudit | None = None)`. Per candidate: `DispatchStarted` (durable, pre-backend) → backend call → `DispatchCompleted` (post-backend) + `CandidateOutcome("success")`; a paid reservation emits `ReservationOpened` before `DispatchStarted`. A pre-dispatch `record` exception raises `RouteAuditError` (candidate NOT advanced; if a reservation opened, it is `release`d + 026 settled). A post-dispatch `record` exception raises `RouteAuditError` (fail closed) with the reservation left `retained`.

- [ ] **Step 1a: Write the failing FREE-path tests (unit file)**

Add to `tests/unit/test_model_selection_execute.py` (real `_chain`/`_free_candidate`/`ScriptedBackend`/`_factory`/`MSG` in scope). Import the real recorders from the T2 module:

```python
# in tests/unit/test_model_selection_execute.py
from llmxive.model_selection.attempt_hooks import RouteAuditError
from tests.unit.test_model_selection_attempt_hooks import _Recorder, _FailingRecorder


def test_route_audit_emits_dispatch_lifecycle_free_chain():
    rec = _Recorder()
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_factory(ScriptedBackend({})), route_audit=rec)
    kinds = [type(e).__name__ for e in rec.events]
    assert kinds == ["DispatchStarted", "DispatchCompleted", "CandidateOutcome"]
    assert rec.events[-1].outcome == "success"


def test_route_audit_predispatch_failure_is_route_fatal():
    rec = _FailingRecorder(fail_on={"DispatchStarted"})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    with pytest.raises(RouteAuditError):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_factory(ScriptedBackend({})), route_audit=rec)
    assert "DispatchCompleted" not in [type(e).__name__ for e in rec.events]


def test_route_audit_none_is_behavior_preserving():
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    result = execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                     backend_factory=_factory(ScriptedBackend({})))
    assert result.response is not None
```

- [ ] **Step 1b: Write the failing PAID post-dispatch test (integration file)**

Add to `tests/integration/test_model_selection_execute.py` (real `repo`/`_paid_chain`/`_observer`/`_balance`/`LOCAL_CFG`/`_ok_factory` from Task 3):

```python
# in tests/integration/test_model_selection_execute.py
from tests.unit.test_model_selection_attempt_hooks import _FailingRecorder


def test_route_audit_postdispatch_failure_fails_closed_retained(repo):
    from llmxive.model_selection.attempt_hooks import RouteAuditError
    budget = _Budget(10_000.0)
    rec = _FailingRecorder(fail_on={"DispatchCompleted"})
    with pytest.raises(RouteAuditError):
        execute(_paid_chain(), MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_ok_factory(), ledger_repo=repo, ledger_config=LOCAL_CFG,
                credit_observer=_observer(), balance_fetch=_balance(),
                reservation_authority=budget, route_audit=rec)
    # Backend ran; audit failed post-dispatch → fail closed, reservation RETAINED (not released).
    assert budget.retained

- [ ] **Step 2: Run tests to verify they fail**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_execute.py tests/integration/test_model_selection_execute.py -k route_audit -q`
Expected: FAIL — `execute() got an unexpected keyword argument 'route_audit'`.

- [ ] **Step 3: Add the param + a durable-emit helper**

Add `route_audit: RouteAudit | None = None` to the `execute` signature (after `reservation_authority`). Add these imports at the top of `execute.py`:

```python
from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    DispatchCompleted,
    DispatchStarted,
    ReservationAuthority,
    ReservationOpened,
    RouteAudit,
    RouteAuditError,
)
```

Add a helper that turns a mandatory-sink failure into the route-fatal error (a `record` that raises is never swallowed — FR-033a):

```python
def _audit(route_audit: RouteAudit | None, event) -> None:
    """Emit one mandatory audit event. A sink exception is NEVER swallowed — it is
    re-raised as RouteAuditError so the caller can apply the route-fatal (pre-dispatch)
    or fail-closed (post-dispatch) rule. A None sink is a no-op."""
    if route_audit is None:
        return
    try:
        route_audit.record(event)
    except RouteAuditError:
        raise
    except Exception as exc:  # noqa: BLE001 — mandatory sink: surface, never swallow
        raise RouteAuditError(f"route_audit.record({type(event).__name__}) failed: {exc}") from exc
```

- [ ] **Step 4: Emit the outbox lifecycle in the candidate loop**

In the per-candidate loop (`execute.py:260-326`), after a paid reservation opens, emit `ReservationOpened`; emit `DispatchStarted` (durable, pre-backend) OUTSIDE the broad `except` so its failure is route-fatal; emit `DispatchCompleted` + `CandidateOutcome("success")` after success; make `RouteAuditError` propagate (it is not a candidate disposition). The loop body becomes:

```python
    for candidate in chain.candidates:
        ref = candidate.model_ref
        reservation_id: str | None = None
        reserved_credits = 0.0

        if not candidate.pricing.is_free:
            if ledger_config_error is not None:
                notes.append(f"paid {ref.model_id!r} skipped: production ledger not configured "
                             f"({ledger_config_error}) — fail closed")
                _audit(route_audit, CandidateOutcome(ref.model_id, "skip", "ledger not configured"))
                continue
            reservation_id, reserved_credits, skip = _open_paid_reservation(
                candidate, chain, options=options, retries=retries,
                ledger_repo=ledger_repo, ledger_config=ledger_config,
                credit_observer=credit_observer, balance_fetch=balance_fetch,
                now=now, call_id=call_id, reservation_authority=reservation_authority,
            )
            if skip is not None:
                notes.append(skip)
                _audit(route_audit, CandidateOutcome(ref.model_id, "skip", skip))
                continue

        # Pre-dispatch audits (FR-033a outbox), durable BEFORE the backend call.
        # A failure of EITHER ReservationOpened OR DispatchStarted is ROUTE-FATAL:
        # do NOT advance. If a reservation opened, release it (definitively did not
        # dispatch) and settle the 026 hold, then re-raise. Both are inside ONE try
        # so a ReservationOpened failure cannot leak the reservation.
        try:
            if reservation_id is not None:
                _audit(route_audit, ReservationOpened(reservation_id, ref.model_id, reserved_credits))
            _audit(route_audit, DispatchStarted(ref.model_id, reservation_id))
        except RouteAuditError:
            if reservation_id is not None:
                if reservation_authority is not None:
                    reservation_authority.release(reservation_id)
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:  # noqa: BLE001
                    logger.warning("execute: settle(%s) after audit-abort failed: %s", reservation_id, exc)
            raise

        lease = (
            ReservationLease(
                ledger_repo, reservation_id,  # type: ignore[arg-type]
                interval_s=max(5.0, lease_duration_for(options.deadline_s) / 3.0),
                lease_duration_s=lease_duration_for(options.deadline_s),
                config=ledger_config,
            )
            if reservation_id is not None
            else nullcontext()
        )
        try:
            backend = backend_factory(ref.backend)
            with lease:
                response = chat_one_candidate(
                    backend, msg_list, model=ref.model_id, max_tokens=options.max_tokens,
                    temperature=options.temperature, deadline_s=options.deadline_s, retries=retries,
                )
            # Post-dispatch (FR-033a/F2): a failure here fails the call CLOSED, but the
            # reservation stays RETAINED (the finally settles/marks it) — the backend
            # already ran, so we never advance.
            _audit(route_audit, DispatchCompleted(ref.model_id, reservation_id))
            _audit(route_audit, CandidateOutcome(ref.model_id, "success", "ok"))
            return ExecutionResult(
                response=response, model_ref=ref, reserved_credits=reserved_credits,
                notes=tuple(notes), reservation_id=reservation_id,
            )
        except RouteAuditError:
            raise  # route-fatal — never a candidate disposition
        except Exception as exc:
            disp = disposition_of(exc)
            if disp is CandidateDisposition.ABORT:
                _audit(route_audit, CandidateOutcome(ref.model_id, "abort", f"{type(exc).__name__}: {exc}"))
                raise
            notes.append(f"{ref.model_id!r}: {disp.value}: {type(exc).__name__}: {exc}")
            _audit(route_audit, CandidateOutcome(ref.model_id, "advance", f"{disp.value}: {type(exc).__name__}"))
        finally:
            if reservation_id is not None:
                try:
                    settle(ledger_repo, reservation_id, now=now, config=ledger_config)  # type: ignore[arg-type]
                except Exception as exc:  # noqa: BLE001
                    logger.warning("execute: settle(%s) failed: %s", reservation_id, exc)
                if reservation_authority is not None:
                    reservation_authority.mark_retained(reservation_id)
```

> Note: the `finally` runs on the `RouteAuditError` post-dispatch path too, so the reservation is settled + `mark_retained` — exactly the FR-033a "fail closed, reservation retained" guarantee. On the pre-dispatch `DispatchStarted` abort we already released before the `lease`/`try` block was entered, so this `finally` never runs for that path.

- [ ] **Step 5: Run tests to verify they pass**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_execute.py tests/integration/test_model_selection_execute.py -k route_audit -q`
Expected: PASS (4 passed — 3 free unit + 1 paid integration).

- [ ] **Step 6: Regression**

Run: `pytest tests/unit/test_model_selection_execute.py tests/integration/test_model_selection_execute.py -q`
Expected: PASS — no audit calls happen when `route_audit is None`.

- [ ] **Step 7: Commit**

```bash
git add src/llmxive/model_selection/execute.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T4): thread route_audit outbox through execute (FR-033a F1/F2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 5: Thread both hooks through `route_chat` (+ selection-failure audit)

`route_chat` is the lane's entry point, so it must accept both hooks, emit `SelectionFailure` when `select` raises `ModelUnavailable` (re-raising it — the reroute logic in slice 1 catches the re-raised `ModelUnavailable`), emit `ChainResolved` on success, and pass both hooks to `execute`.

**Files:**
- Modify: `src/llmxive/model_selection/route.py` — `route_chat` signature (`:132-148`), the `select` call region (`:222-227`), the `execute` call (`:232-241`)
- Test: `tests/unit/test_model_selection_attempt_hooks.py`

**Interfaces:**
- Consumes: `ReservationAuthority`, `RouteAudit`, the event types, `ModelUnavailable`.
- Produces: `route_chat(..., reservation_authority: ReservationAuthority | None = None, route_audit: RouteAudit | None = None) -> ChatResponse` (return type unchanged — the audit sink is the structured channel). Emits `SelectionFailure` then re-raises on `ModelUnavailable`; emits `ChainResolved` after the final `select`; forwards both hooks to `execute`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit/test_model_selection_route.py`, reusing its snapshot builder. Confirm the exact name of that file's snapshot helper first (grep the file — it is the `_snapshot(...)` builder mirroring `tests/unit/test_model_selection_select.py:51`, which defaults to an eligible free chain); `_no_eligible_snapshot()` below is a `_snapshot(model_ids=[…])` restricted so `select` raises `ModelUnavailable` (e.g. a single vision-only family for a `standard_generation` call — the same technique `test_model_selection_select.py` uses to force `ModelUnavailable`). Import the recorder from the T2 module.

```python
# in tests/unit/test_model_selection_route.py
from llmxive.model_selection import route_chat
from llmxive.model_selection.attempt_hooks import ChainResolved, SelectionFailure
from llmxive.model_selection.types import ModelUnavailable
from llmxive.backends.base import ChatMessage
from tests.unit.test_model_selection_attempt_hooks import _Recorder


def test_route_chat_emits_chain_resolved():
    rec = _Recorder()
    route_chat([ChatMessage(role="user", content="hi")], profile="standard_generation",
               max_tokens=32, snapshot=_snapshot(), route_audit=rec)  # default = eligible
    assert any(isinstance(e, ChainResolved) for e in rec.events)


def test_route_chat_emits_selection_failure_and_reraises():
    rec = _Recorder()
    with pytest.raises(ModelUnavailable):
        route_chat([ChatMessage(role="user", content="hi")], profile="standard_generation",
                   max_tokens=32, snapshot=_no_eligible_snapshot(), route_audit=rec)
    assert any(isinstance(e, SelectionFailure) for e in rec.events)
```

> If `route_chat` in this test module normally acquires its own snapshot (no `snapshot=` seam used elsewhere in the file), the `snapshot=` injection param at `route.py:144` is the sanctioned test seam — use it. Do NOT stub `runtime_snapshot`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_route.py -k "emits_chain_resolved or emits_selection_failure" -q`
Expected: FAIL — `route_chat() got an unexpected keyword argument 'route_audit'`.

- [ ] **Step 3: Add params + a `select`-with-audit wrapper**

Add the two params to `route_chat` (`route.py:132-148`, after `overrides`). Add imports at the top of `route.py`:

```python
from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    ReservationAuthority,
    RouteAudit,
    SelectionFailure,
)
from llmxive.model_selection.types import ModelUnavailable  # add to the existing types import
```

Add a helper (module level) that emits `SelectionFailure` on `ModelUnavailable` and re-raises:

```python
def _select_audited(requirement, snap, route_audit: RouteAudit | None):
    """Run select; on ModelUnavailable emit a SelectionFailure audit event (so the
    proposal reroute's failed first leg is auditable, FR-002/F3) and RE-RAISE — the
    caller's fail-closed / reroute logic is unchanged. A route_audit failure here is
    itself route-fatal (RouteAuditError propagates)."""
    try:
        return select(requirement, snap)
    except ModelUnavailable as exc:
        if route_audit is not None:
            prov = ",".join(f"{k}={v.source}" for k, v in snap.sources.items())
            route_audit.record(SelectionFailure(
                exception_type=type(exc).__name__, message=str(exc),
                requirement_digest=snap.digest, snapshot_provenance=prov,
            ))
        raise
```

- [ ] **Step 4: Use the wrapper + emit `ChainResolved` + forward hooks**

Replace the two `select(...)` calls in `route_chat` (the `exclude_leader` pass-1 at `route.py:222` and THE decision at `:226`) with `_select_audited(...)`, emit `ChainResolved` after `_promote_primary`, and pass both hooks to `execute`:

```python
    if overrides is not None and overrides.exclude_leader:
        leader = _select_audited(requirement, snap, route_audit).candidates[0].model_ref.model_id
        requirement = replace(requirement, exclude_models=requirement.exclude_models | {leader})
    chain = _select_audited(requirement, snap, route_audit)   # THE decision
    chain = _promote_primary(chain, caller_model)

    if route_audit is not None:
        route_audit.record(ChainResolved(
            snapshot_digest=chain.snapshot_digest,
            selection_policy_version=chain.selection_policy_version,
            resolved_at=chain.resolved_at.isoformat(),
            explanation=chain.explanation,
            candidate_model_ids=tuple(c.model_ref.model_id for c in chain.candidates),
        ))

    options = ExecutionOptions(max_tokens=max_tokens, temperature=temperature, deadline_s=deadline_s)
    result = execute(
        chain, msg_list, options=options, backend_factory=backend_factory, retries=retries,
        ledger_repo=ledger_repo, ledger_config=ledger_config,
        reservation_authority=reservation_authority, route_audit=route_audit,
    )
    return result.response
```

> The bare `route_audit.record(ChainResolved(...))` here (not via `_audit`) is intentional: a `ChainResolved`/`SelectionFailure` sink failure is pre-dispatch and route-fatal, so letting the raw exception propagate is correct. If you prefer the uniform `RouteAuditError` wrapping, import and use the `_audit` helper from `execute.py` — but do NOT swallow.

- [ ] **Step 5: Run tests to verify they pass**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_route.py -k "emits_chain_resolved or emits_selection_failure" -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Regression**

Run: `pytest tests/unit/test_model_selection_route.py -q`
Expected: PASS — `route_chat` with no hooks is unchanged.

- [ ] **Step 7: Commit**

```bash
git add src/llmxive/model_selection/route.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T5): thread reservation_authority + route_audit through route_chat

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 6: Public exports + full-suite regression gate + real-call sanity

Export the new public names, then prove the whole invariant: default behavior is byte-for-byte unchanged (full non-slow suite green) and the paid path still works against a real Dartmouth call.

**Files:**
- Modify: `src/llmxive/model_selection/__init__.py` (`__all__` + eager exports for the pure `attempt_hooks` types)
- Test: whole suite

**Interfaces:**
- Produces: `from llmxive.model_selection import ReservationAuthority, RouteAudit, RouteAuditError` (+ the event dataclasses) resolves. These are pure types, so export them EAGERLY (unlike `route_chat`/`runtime_snapshot`, which stay lazy in `__getattr__` because they import the networked snapshot layer).

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/test_model_selection_attempt_hooks.py
def test_public_exports_resolve():
    import llmxive.model_selection as ms
    for name in ("ReservationAuthority", "RouteAudit", "RouteAuditError",
                 "ChainResolved", "SelectionFailure", "ReservationOpened",
                 "DispatchStarted", "DispatchCompleted", "DispatchUnknown",
                 "CandidateOutcome"):
        assert hasattr(ms, name), name


def test_eager_export_does_not_load_networked_snapshot():
    # attempt_hooks is pure types; importing the package must NOT pull in the
    # networked snapshot layer (the laziness 026 preserves).
    import sys
    import importlib
    for m in list(sys.modules):
        if m.startswith("llmxive.model_selection"):
            del sys.modules[m]
    importlib.import_module("llmxive.model_selection")
    assert "llmxive.model_selection.snapshot" not in sys.modules
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -k exports -q`
Expected: FAIL — `AttributeError: module 'llmxive.model_selection' has no attribute 'ReservationAuthority'`.

- [ ] **Step 3: Add the eager exports**

In `src/llmxive/model_selection/__init__.py`, add an import block (near the other eager imports) and extend `__all__`:

```python
from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    ChainResolved,
    DispatchCompleted,
    DispatchStarted,
    DispatchUnknown,
    ReservationAuthority,
    ReservationOpened,
    RouteAudit,
    RouteAuditError,
    SelectionFailure,
)
```

Add those ten names to `__all__` (keep it sorted, matching the existing style). Do NOT add `route_chat`/`runtime_snapshot` handling — those remain in `__getattr__`.

- [ ] **Step 4: Run the export tests**

Run: `PRE_COMMIT_ALLOW_NO_CONFIG=1 pytest tests/unit/test_model_selection_attempt_hooks.py -k exports -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Full non-slow suite (THE regression gate)**

Run: `pytest tests/unit tests/contract tests/integration -m "not slow" -q`
Expected: **7123+ passed, 0 failed** (the new file adds tests; the baseline stays green). If ANY previously-green test now fails, the default-behavior invariant was broken — fix the code, never the test.

- [ ] **Step 6: Enforcement guard still green**

Run: `pytest tests/unit/test_model_selection_enforcement.py -q` (or the file that exercises `enforcement.find_violations`)
Expected: PASS — slice 0 added no model-id pins.

- [ ] **Step 7: Real-call sanity (the paid-guard path every real call crosses)**

Run: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_vision_real.py -q` (needs `DARTMOUTH_CHAT_API_KEY`; if absent, run the `local`-backend equivalent per CLAUDE.md and note it).
Expected: PASS — a live `route_chat` with no hooks behaves exactly as before.

- [ ] **Step 8: Commit**

```bash
git add src/llmxive/model_selection/__init__.py tests/unit/test_model_selection_attempt_hooks.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(025 slice-0 T6): export attempt hooks; full-suite + real-call regression gate

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

## Slice 0 Definition of Done

- `ExecutionResult.reservation_id`, `ReservationAuthority`, `RouteAudit` (+ events + `RouteAuditError`) exist and are exported.
- `route_chat`/`execute` accept `reservation_authority` + `route_audit`; with both `None` behavior is byte-for-byte unchanged (full non-slow suite green, real-call green).
- The FR-033(b) ordering + rollback (reserve-Attempt → reserve-026 → dispatch; refuse→skip, 026-fail→release, dispatched→retained) is implemented and tested.
- The FR-033(a) outbox lifecycle + route-fatal pre-dispatch + fail-closed post-dispatch is implemented and tested.
- `SelectionFailure`/`ChainResolved` are emitted around `select`; `ModelUnavailable` still propagates (the reroute is slice 1).
- No push. Ready for slice 1 to build the `AttemptCreditLedger` (the real `ReservationAuthority`) and the event-sourced `RouteAudit` sink on top of these contracts.
