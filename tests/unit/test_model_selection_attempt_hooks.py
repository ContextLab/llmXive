import subprocess
import sys

from llmxive.model_selection.attempt_hooks import (
    ChainResolved,
    DispatchStarted,
    ReservationAuthority,
    RouteAudit,
    RouteAuditError,
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


def test_reservation_authority_is_structural():
    b = _Budget(10.0)
    assert isinstance(b, ReservationAuthority)
    assert b.reserve(4.0, reservation_id="r1", call_id="c1") is True
    assert b.reserve(7.0, reservation_id="r2", call_id="c1") is False  # over cap


def test_route_audit_is_structural_and_records_events():
    rec = _Recorder()
    assert isinstance(rec, RouteAudit)
    rec.record(ChainResolved(
        route_id="R", requirement_digest="rq", prompt_digest="pd", context_digest="cd",
        snapshot_digest="d", snapshot_provenance={}, selection_policy_version=1,
        resolved_at="t", explanation=(), candidates=(_ref(),),
    ))
    rec.record(DispatchStarted(route_id="R", candidate_index=0, candidate=_ref(), reservation_id=None))
    assert len(rec.events) == 2


def test_route_audit_error_is_runtime_error():
    assert issubclass(RouteAuditError, RuntimeError)
    assert not issubclass(RouteAuditError, ValueError)


def test_selection_failure_carries_structured_reason():
    ev = SelectionFailure(route_id="R", exception_type="ModelUnavailable", message="none eligible",
                          requirement_digest="rq", snapshot_provenance={})
    assert ev.exception_type == "ModelUnavailable"


def test_public_exports_resolve():
    import llmxive.model_selection as ms
    for name in ("ReservationAuthority", "RouteAudit", "RouteAuditError",
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
