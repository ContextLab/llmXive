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
