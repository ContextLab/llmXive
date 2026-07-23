import subprocess
import sys
import threading

import pytest

from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchStarted,
    ReservationAuthority,
    RouteAudit,
    RouteAuditError,
    RouteReplayError,
    SelectionFailure,
)
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


class _Budget:
    """A REAL in-memory ReservationAuthority: an Attempt budget counter.

    Collision semantics (spec-025 maintainer review fix #5, ``attempt_hooks.
    ReservationAuthority.reserve``'s docstring, mirroring the 026 ledger's own
    ``reserve``): a repeated ``reservation_id`` with the SAME ``(credits,
    call_id)`` identity is an idempotent success (no double-count); the SAME
    ``reservation_id`` with a DIFFERENT identity is an integrity violation
    (raise) — never silently overwrite the existing hold."""
    def __init__(self, cap: float):
        self.cap = cap
        self.open: dict[str, float] = {}
        self._call_ids: dict[str, str] = {}
        self.retained: set[str] = set()
        self.released: set[str] = set()

    def reserve(self, credits: float, *, reservation_id: str, call_id: str) -> bool:
        existing = self.open.get(reservation_id)
        if existing is not None:
            if existing != credits or self._call_ids.get(reservation_id) != call_id:
                raise ValueError(
                    f"reservation id {reservation_id!r} COLLISION: existing (credits="
                    f"{existing}, call_id={self._call_ids.get(reservation_id)!r}) != "
                    f"requested (credits={credits}, call_id={call_id!r})"
                )
            return True  # idempotent: already reserved, no double-count
        if sum(self.open.values()) + credits > self.cap:
            return False
        self.open[reservation_id] = credits
        self._call_ids[reservation_id] = call_id
        return True

    def release(self, reservation_id: str) -> None:
        self.open.pop(reservation_id, None)
        self._call_ids.pop(reservation_id, None)
        self.released.add(reservation_id)

    def mark_retained(self, reservation_id: str) -> None:
        self.retained.add(reservation_id)


class _Recorder:
    """A REAL in-memory RouteAudit sink. ``claim_dispatch`` is NAIVE (no dedup,
    always claims) — this double intentionally does NOT implement the fix #5
    atomicity contract; ``_ClaimingRecorder`` below is the one that does."""
    def __init__(self):
        self.events: list = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


class _FailingRecorder:
    """A REAL in-memory RouteAudit sink that raises on a chosen set of event
    types (matched by class name) and records every other event — used to
    exercise the mandatory outbox's route-fatal (pre-dispatch) / fail-closed
    (post-dispatch) rules without mocking the sink itself."""
    def __init__(self, fail_on: set[str]):
        self.fail_on = fail_on
        self.events: list = []

    def record(self, event) -> None:
        if type(event).__name__ in self.fail_on:
            raise RuntimeError(f"simulated route_audit sink failure on {type(event).__name__}")
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        if "DispatchStarted" in self.fail_on:
            raise RuntimeError("simulated route_audit sink failure on DispatchStarted")
        self.events.append(event)
        return True


class _ClaimingRecorder:
    """A REAL in-memory RouteAudit sink implementing the ATOMIC dispatch-claim
    boundary (spec-025 maintainer review fix #5): a ``threading.Lock``-guarded
    set of claimed ``DispatchStarted`` event_ids ensures exactly one claimant
    wins per event_id, even under concurrent callers (a compare-and-swap /
    unique-insert, not a read-then-write). ``record`` follows the round-4 (F2)
    collision semantics: idempotent on an identical payload, integrity-raise
    (``ValueError``, normalized by ``emit_audit``/the claim-exception handler to
    ``RouteAuditError``) on a conflicting one."""

    def __init__(self):
        self._lock = threading.Lock()
        self._claimed: set[str] = set()
        self._by_id: dict[str, tuple] = {}
        self.events: list = []

    @staticmethod
    def _canonical_payload(event) -> tuple:
        return tuple(sorted(vars(event).items()))

    def _record_locked(self, event, payload: tuple) -> None:
        existing = self._by_id.get(event.event_id)
        if existing is not None:
            if existing == payload:
                return  # idempotent replay of the SAME event — no duplicate, no error
            raise ValueError(f"event_id payload mismatch for {event.event_id!r}")
        self._by_id[event.event_id] = payload
        self.events.append(event)

    def record(self, event) -> None:
        payload = self._canonical_payload(event)
        with self._lock:
            self._record_locked(event, payload)

    def claim_dispatch(self, event) -> bool:
        payload = self._canonical_payload(event)
        with self._lock:
            if event.event_id in self._claimed:
                return False
            self._claimed.add(event.event_id)
            self._record_locked(event, payload)
            return True


def test_reservation_authority_is_structural():
    b = _Budget(10.0)
    assert isinstance(b, ReservationAuthority)
    assert b.reserve(4.0, reservation_id="r1", call_id="c1") is True
    assert b.reserve(7.0, reservation_id="r2", call_id="c1") is False  # over cap


# --------------------------------------------------------------------------- #
# F3 (spec-025 maintainer review fix #5): ReservationAuthority.reserve collision
# semantics — a repeated reservation_id with the SAME (credits, call_id) is an
# idempotent success (no double-count); a DIFFERENT identity under the SAME id
# is an integrity violation (raise). ``_Budget`` must enforce both, mirroring
# the 026 ledger's own reserve() (reservations.py ~236-255).
# --------------------------------------------------------------------------- #


def test_budget_reserve_same_id_same_identity_is_idempotent_no_double_count():
    b = _Budget(10.0)
    assert b.reserve(6.0, reservation_id="r1", call_id="c1") is True
    # Repeat with the IDENTICAL (credits, call_id) — idempotent success, and the
    # budget must NOT be double-counted (else a 3rd distinct reservation of 5.0
    # would wrongly be refused: 6+6+5=17 > 10, but 6+5=11 > 10 still refuses —
    # use a value that only fits if the repeat did NOT double-count).
    assert b.reserve(6.0, reservation_id="r1", call_id="c1") is True
    assert b.reserve(4.0, reservation_id="r2", call_id="c2") is True  # 6+4=10, fits
    assert sum(b.open.values()) == 10.0  # NOT 16.0 — the repeat did not double-count


def test_budget_reserve_same_id_different_credits_raises_integrity_error():
    b = _Budget(10.0)
    assert b.reserve(6.0, reservation_id="r1", call_id="c1") is True
    with pytest.raises(ValueError, match="COLLISION"):
        b.reserve(7.0, reservation_id="r1", call_id="c1")  # same id, different credits


def test_budget_reserve_same_id_different_call_id_raises_integrity_error():
    b = _Budget(10.0)
    assert b.reserve(6.0, reservation_id="r1", call_id="c1") is True
    with pytest.raises(ValueError, match="COLLISION"):
        b.reserve(6.0, reservation_id="r1", call_id="c2")  # same id, different call_id


def test_route_audit_is_structural_and_records_events():
    rec = _Recorder()
    assert isinstance(rec, RouteAudit)
    rec.record(ChainResolved(
        route_id="R", requirement_digest="rq", prompt_digest="pd", context_digest="cd",
        snapshot_digest="d", snapshot_provenance={}, selection_policy_version=1,
        resolved_at="t", explanation=(), candidates=(_ref(),),
    ))
    started = DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id=None)
    assert rec.claim_dispatch(started) is True
    assert len(rec.events) == 2


def test_route_audit_error_is_runtime_error():
    assert issubclass(RouteAuditError, RuntimeError)
    assert not issubclass(RouteAuditError, ValueError)


def test_route_replay_error_is_runtime_error():
    assert issubclass(RouteReplayError, RuntimeError)
    assert not issubclass(RouteReplayError, ValueError)
    assert not issubclass(RouteReplayError, RouteAuditError)
    assert not issubclass(RouteAuditError, RouteReplayError)


def test_selection_failure_carries_structured_reason():
    ev = SelectionFailure(route_id="R", exception_type="ModelUnavailable", message="none eligible",
                          requirement_digest="rq", snapshot_provenance={})
    assert ev.exception_type == "ModelUnavailable"


def test_public_exports_resolve():
    import llmxive.model_selection as ms
    for name in ("ReservationAuthority", "RouteAudit", "RouteAuditError", "RouteReplayError",
                 "ChainResolved", "SelectionFailure", "ReservationOpened",
                 "DispatchStarted", "DispatchCompleted", "DispatchUnknown",
                 "CandidateOutcome", "emit_audit"):
        assert hasattr(ms, name), name


def test_event_id_is_deterministic_within_a_route():
    # F1: event_id is auto-derived from route_id + (candidate_index, kind) — so a
    # reconciler can recompute the SAME id twice for the SAME logical event, without
    # any extra state, and pair a DispatchStarted with its DispatchCompleted.
    started = DispatchStarted(route_id="R", candidate_index=2, candidate=_ref(), reservation_id=None)
    assert started.event_id == "R:candidate:2:dispatch-started"

    resolved = ChainResolved(
        route_id="R", requirement_digest="rq", prompt_digest="pd", context_digest="cd",
        snapshot_digest="d", snapshot_provenance={}, selection_policy_version=1,
        resolved_at="t", explanation=(), candidates=(_ref(),),
    )
    assert resolved.event_id == "R:chain-resolved"


def test_eager_export_does_not_load_networked_snapshot():
    # attempt_hooks is pure types; importing the package must NOT pull in the
    # networked snapshot layer (the laziness 026 preserves).
    #
    # sys.modules is process-wide: a delete-then-reimport of
    # llmxive.model_selection.* IN THIS PROCESS (even carefully saved and
    # restored afterward) creates transient new class/module objects and
    # rebinds the parent llmxive package's own `.model_selection` attribute
    # as a side effect of Python's import machinery — corrupting
    # isinstance/exception identity and monkeypatch attribute resolution for
    # any other test in this session that already bound the originals. A
    # subprocess gives a genuinely clean interpreter, so the only thing this
    # test observes is the one import under test, with zero leakage into the
    # running test process.
    code = (
        "import sys, importlib; "
        "importlib.import_module('llmxive.model_selection'); "
        "assert 'llmxive.model_selection.snapshot' not in sys.modules, "
        "'eager package import pulled in the networked snapshot module'"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
