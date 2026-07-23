"""Execution-adapter tests — the FREE / disposition / fail-fast paths (spec 026,
slice 3, US3 / FR-010). Real contract objects + real router safeguards through a
scripted backend (no mocks of the code under test — the fake backend is the
injected seam FR-015 sanctions). The paid reservation-ledger path is covered by
``tests/integration/test_model_selection_execute.py`` against a real git ledger.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    ModelDownError,
    PaidGuardDenied,
    PermanentBackendError,
)
from llmxive.model_selection.attempt_hooks import RouteAuditError, RouteReplayError
from llmxive.model_selection.execute import ChainExhausted, ExecutionResult, execute
from llmxive.model_selection.types import (
    CallBudget,
    Candidate,
    ExecutionOptions,
    ModelChain,
    ModelPricing,
    ModelRef,
    SnapshotProvenance,
)
from tests.unit.test_model_selection_attempt_hooks import (
    _ClaimingRecorder,
    _FailingRecorder,
    _Recorder,
)

NOW = datetime(2026, 7, 16, 12, 0, 0, tzinfo=UTC)
EP = "https://chat.dartmouth.edu"


def _ref(model_id: str, *, backend: str = "dartmouth") -> ModelRef:
    return ModelRef(backend, EP if backend != "local" else "local", model_id, model_id.split(".")[0], "v")


def _free_candidate(model_id: str) -> Candidate:
    return Candidate(_ref(model_id), ModelPricing(0.0, 0.0), 0.0, 0.0)


def _chain(*candidates: Candidate, credit_source: str = "live", budget: CallBudget | None = None) -> ModelChain:
    return ModelChain(
        candidates=tuple(candidates),
        resolved_at=NOW,
        call_budget=budget or CallBudget(max_input_tokens=100_000, max_output_tokens=4096),
        snapshot_digest="D",
        snapshot_provenance={
            "catalog": SnapshotProvenance("live", NOW, 0.0),
            "credit": SnapshotProvenance(credit_source, NOW, 0.0),
        },
        selection_policy_version=1,
    )


class ScriptedBackend:
    """One fake backend that dispatches per-``model``: ``"ok"`` returns a response;
    an ``Exception`` instance is raised. Records every call's kwargs."""

    def __init__(self, script: dict[str, object]):
        self.script = script
        self.calls: list[dict] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.calls.append(
            {"model": model, "max_tokens": max_tokens, "temperature": temperature, "deadline_s": deadline_s}
        )
        behavior = self.script.get(model, "ok")
        if isinstance(behavior, BaseException):
            raise behavior
        return ChatResponse(text=f"ok:{model}", model=model or "m", backend="scripted")


def _factory(backend: ScriptedBackend):
    return lambda name: backend


MSG = [ChatMessage(role="user", content="hello")]


# --------------------------------------------------------------------------- #
# Free-path success + ExecutionOptions propagation
# --------------------------------------------------------------------------- #


def test_free_success_returns_result():
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be))
    assert isinstance(res, ExecutionResult)
    assert res.response.text == "ok:qwen.qwen3.5-122b"
    assert res.model_ref.model_id == "qwen.qwen3.5-122b"
    assert res.reserved_credits == 0.0
    assert res.notes == ()


def test_execution_options_applied_to_candidate():
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    execute(
        chain, MSG,
        options=ExecutionOptions(max_tokens=777, temperature=0.4, deadline_s=123.0),
        backend_factory=_factory(be), retries=1,
    )
    assert be.calls[0] == {"model": "qwen.qwen3.5-122b", "max_tokens": 777, "temperature": 0.4, "deadline_s": 123.0}


# --------------------------------------------------------------------------- #
# The three per-candidate dispositions (FR-010 / SC-006)
# --------------------------------------------------------------------------- #


def test_transient_advances_to_next_candidate():
    be = ScriptedBackend({"qwen.qwen3.5-122b": ModelDownError("vLLM hang")})  # no-retry transient → advance
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), _free_candidate("google.gemma-4-31B-it"))
    res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be), retries=1)
    assert res.model_ref.model_id == "google.gemma-4-31B-it"
    assert len(res.notes) == 1 and "retry_advance" in res.notes[0]


def test_breaker_open_advances():
    be = ScriptedBackend({"qwen.qwen3.5-122b": BackendUnavailable("breaker open")})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), _free_candidate("google.gemma-4-31B-it"))
    res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be), retries=1)
    assert res.model_ref.model_id == "google.gemma-4-31B-it"


def test_paid_guard_denial_skips_candidate():
    be = ScriptedBackend({"qwen.qwen3.5-122b": PaidGuardDenied("budget cap reached")})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), _free_candidate("google.gemma-4-31B-it"))
    res = execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be), retries=1)
    assert res.model_ref.model_id == "google.gemma-4-31B-it"
    assert "skip" in res.notes[0]


def test_permanent_refusal_aborts_and_does_not_advance():
    be = ScriptedBackend({"qwen.qwen3.5-122b": PermanentBackendError("bad request 400")})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), _free_candidate("google.gemma-4-31B-it"))
    with pytest.raises(PermanentBackendError):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be), retries=1)
    # gemma was never tried — abort stops the chain
    assert [c["model"] for c in be.calls] == ["qwen.qwen3.5-122b"]


def test_all_transient_raises_chain_exhausted():
    be = ScriptedBackend(
        {"qwen.qwen3.5-122b": ModelDownError("down"), "google.gemma-4-31B-it": ModelDownError("down")}
    )
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), _free_candidate("google.gemma-4-31B-it"))
    with pytest.raises(ChainExhausted) as ei:
        execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be), retries=1)
    assert "exhausted" in str(ei.value)


# --------------------------------------------------------------------------- #
# Fail-fast budget check (FR-010 / US3 scenario 5) — BEFORE any call
# --------------------------------------------------------------------------- #


def test_fail_fast_input_too_large():
    be = ScriptedBackend({})
    tiny = CallBudget(max_input_tokens=5, max_output_tokens=4096)
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), budget=tiny)
    big = [ChatMessage(role="user", content="x" * 500)]
    with pytest.raises(ValueError, match="fail-fast"):
        execute(chain, big, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be))
    assert be.calls == []  # never called


def test_fail_fast_output_exceeds_budget():
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"), budget=CallBudget(100_000, max_output_tokens=256))
    with pytest.raises(ValueError, match="fail-fast"):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=999), backend_factory=_factory(be))
    assert be.calls == []


def test_empty_chain_raises_chain_exhausted():
    with pytest.raises(ChainExhausted):
        execute(_chain(), MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(ScriptedBackend({})))


# --------------------------------------------------------------------------- #
# Paid candidate WITHOUT a ledger / non-live credit → fail-closed skip (no call)
# --------------------------------------------------------------------------- #


def _paid_candidate(model_id: str = "anthropic.claude-haiku-4-5-20251001") -> Candidate:
    return Candidate(_ref(model_id), ModelPricing(1e-6, 5e-6), 2.5, 500.0)


def test_paid_candidate_skipped_without_ledger():
    be = ScriptedBackend({})
    chain = _chain(_paid_candidate())  # ledger_repo not provided
    with pytest.raises(ChainExhausted) as ei:
        execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be))
    assert "no reservation ledger" in str(ei.value)
    assert be.calls == []  # paid candidate never called (fail closed)


def test_paid_candidate_skipped_on_non_live_credit_snapshot():
    # C6: even with a ledger, a chain whose credit snapshot was NOT live must not
    # admit a paid call. Here there is no ledger EITHER, but the C6 gate fires first.
    be = ScriptedBackend({})
    chain = _chain(_paid_candidate(), credit_source="last_known_good")
    with pytest.raises(ChainExhausted) as ei:
        execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=_factory(be))
    assert "C6" in str(ei.value) and "live" in str(ei.value)
    assert be.calls == []


# --------------------------------------------------------------------------- #
# Task 4 (spec 025 slice-0): route_audit outbox lifecycle threaded through
# execute (FR-033a) — the FREE-path cases. The PAID post-dispatch fail-closed
# case lives in tests/integration/test_model_selection_execute.py (it needs
# the real ledger fixture to open an actual reservation).
# --------------------------------------------------------------------------- #


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


def test_concurrent_same_model_calls_are_distinguishable_by_route_id():
    # F1: two independent execute() calls for the SAME free model, each with its
    # OWN recorder, must carry DIFFERENT route_id/event_id on their DispatchStarted/
    # DispatchCompleted events — otherwise a reconciler could not tell which
    # DispatchCompleted pairs with which DispatchStarted when two calls for the
    # same model are in flight at once. execute() generates a random route_id when
    # none is passed, so two calls must differ.
    rec1, rec2 = _Recorder(), _Recorder()
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_factory(ScriptedBackend({})), route_audit=rec1)
    execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_factory(ScriptedBackend({})), route_audit=rec2)

    started1 = next(e for e in rec1.events if type(e).__name__ == "DispatchStarted")
    completed1 = next(e for e in rec1.events if type(e).__name__ == "DispatchCompleted")
    started2 = next(e for e in rec2.events if type(e).__name__ == "DispatchStarted")
    completed2 = next(e for e in rec2.events if type(e).__name__ == "DispatchCompleted")

    # Same route → DispatchStarted and DispatchCompleted pair by route_id.
    assert started1.route_id == completed1.route_id
    assert started2.route_id == completed2.route_id
    # Different routes → distinguishable route_id and event_id.
    assert started1.route_id != started2.route_id
    assert started1.event_id != started2.event_id
    assert completed1.event_id != completed2.event_id


# --------------------------------------------------------------------------- #
# Slice-0 audit fix #2 (MEDIUM): RouteAudit event_id collision semantics — a
# durable sink must treat a REPLAYED event_id with a byte-identical payload as
# an idempotent success, and a CONFLICTING payload under the same event_id as
# an integrity violation that MUST raise (never a silently-accepted duplicate).
# emit_audit normalizes that raise to RouteAuditError (route-fatal).
# --------------------------------------------------------------------------- #


class _CollisionDetectingRecorder:
    """A REAL stateful ``RouteAudit`` sink (no mock) implementing the F2 contract
    from ``attempt_hooks.RouteAudit.record``'s docstring: events are stored by
    ``event_id``; a second ``record()`` of an event_id already stored with a
    BYTE-IDENTICAL canonical payload is an idempotent no-op (no duplicate, no
    error); a second ``record()`` of the SAME event_id with a DIFFERENT payload
    raises a plain ``ValueError`` — exactly the "sink integrity error" case
    ``emit_audit`` must normalize to ``RouteAuditError``.

    ``claim_dispatch`` here is deliberately NAIVE (delegates to ``record`` and
    always returns ``True``) — this double exists to exercise F2's EVENT-payload
    collision semantics specifically, not fix #5's dispatch-boundary atomicity
    (``_ClaimingRecorder`` in ``test_model_selection_attempt_hooks.py`` is the one
    that implements that); its two tests below are unaffected by fix #5 because
    they never assert a backend-call count."""

    def __init__(self):
        self._by_id: dict[str, tuple] = {}
        self.events: list = []

    @staticmethod
    def _canonical_payload(event) -> tuple:
        # Dataclass events → their field dict, projected to a stable, orderable
        # tuple of (field_name, value) pairs (field names are unique, so sorting
        # never needs to compare two values against each other).
        return tuple(sorted(vars(event).items()))

    def record(self, event) -> None:
        payload = self._canonical_payload(event)
        existing = self._by_id.get(event.event_id)
        if existing is not None:
            if existing == payload:
                return  # idempotent replay of the SAME event — no duplicate, no error
            raise ValueError(f"event_id payload mismatch for {event.event_id!r}")
        self._by_id[event.event_id] = payload
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.record(event)
        return True


def test_route_audit_replayed_identical_event_is_idempotent_no_error():
    # Same route_id + same chain → every emitted event_id/payload pair is
    # byte-identical across the two calls; the sink must accept the replay
    # silently (no duplicate stored, no exception).
    rec = _CollisionDetectingRecorder()
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    for _ in range(2):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_factory(ScriptedBackend({})), route_audit=rec, route_id="replay-route")
    # Recorded ONCE per event_id, not twice — the replay was a no-op.
    kinds = [type(e).__name__ for e in rec.events]
    assert kinds == ["DispatchStarted", "DispatchCompleted", "CandidateOutcome"]


def test_route_audit_conflicting_payload_same_event_id_raises_route_fatal_not_raw_error():
    # F2: DispatchStarted's event_id is derived from (route_id, candidate_index,
    # kind) ONLY — not from the candidate identity. So a SECOND execute() call
    # reusing the same route_id but a DIFFERENT chain (different candidate at
    # index 0) produces a DispatchStarted with the SAME event_id but a DIFFERENT
    # payload — a genuine conflict. The sink raises a plain ValueError;
    # execute()/emit_audit MUST surface RouteAuditError (route-fatal), never let
    # the raw ValueError leak. Non-vacuous: RouteAuditError is NOT a ValueError
    # subclass (see test_route_audit_error_is_runtime_error), so this only
    # passes if emit_audit actually normalizes the sink's exception.
    rec = _CollisionDetectingRecorder()
    chain_a = _chain(_free_candidate("qwen.qwen3.5-122b"))
    chain_b = _chain(_free_candidate("google.gemma-4-31B-it"))  # DIFFERENT candidate, same index
    execute(chain_a, MSG, options=ExecutionOptions(max_tokens=64),
            backend_factory=_factory(ScriptedBackend({})), route_audit=rec, route_id="conflict-route")
    with pytest.raises(RouteAuditError):
        execute(chain_b, MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_factory(ScriptedBackend({})), route_audit=rec, route_id="conflict-route")
    # The second call's DispatchCompleted/CandidateOutcome never happened — the
    # conflict was caught pre-dispatch (the first event emitted), route-fatal.
    kinds = [type(e).__name__ for e in rec.events]
    assert kinds.count("DispatchStarted") == 1  # chain_a's; chain_b's raised before storing
    assert "DispatchCompleted" in kinds and kinds.count("DispatchCompleted") == 1  # only chain_a's


# --------------------------------------------------------------------------- #
# Spec-025 maintainer review fix #5: an ATOMIC dispatch-claim boundary so a
# replayed logical route (same route_id) does NOT re-invoke the backend. Round
# 4 made the audit EVENTS idempotent but left the SIDE EFFECT (backend dispatch)
# un-deduplicated — these tests assert the backend-call COUNT, not just event
# shape. The PAID sequential/concurrent/replay-before-complete cases (which need
# the real ledger + a reservation) live in
# tests/integration/test_model_selection_execute.py.
# --------------------------------------------------------------------------- #


def test_free_replay_same_route_id_does_not_redispatch_backend():
    # Sequential same-route (FREE): backend called exactly once. The first
    # execute() call dispatches and succeeds; a second call for the SAME
    # route_id, sharing the SAME _ClaimingRecorder, must NOT invoke the backend
    # again — it raises RouteReplayError instead.
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    rec = _ClaimingRecorder()
    route_id = "free-replay-route"

    result1 = execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                      backend_factory=_factory(be), route_audit=rec, route_id=route_id)
    assert result1.response is not None

    with pytest.raises(RouteReplayError):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_factory(be), route_audit=rec, route_id=route_id)

    assert len(be.calls) == 1  # the replay did NOT re-invoke the backend


def test_replay_before_dispatch_completed_never_dispatches_free():
    # Replay after DispatchStarted, before DispatchCompleted, never re-dispatches:
    # pre-claim the recorder for the candidate's DispatchStarted event_id BEFORE
    # calling execute() at all (simulating a crash/retry between DispatchStarted
    # and DispatchCompleted) — execute() must see claimed=False immediately and
    # never touch the backend for THIS call.
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    rec = _ClaimingRecorder()
    route_id = "pre-claimed-route"

    from llmxive.model_selection.attempt_hooks import DispatchStarted

    pre_started = DispatchStarted(
        route_id=route_id, candidate_index=0, candidate=_ref("qwen.qwen3.5-122b"), reservation_id=None,
    )
    assert rec.claim_dispatch(pre_started) is True  # simulates the ORIGINAL dispatch's claim

    with pytest.raises(RouteReplayError):
        execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                backend_factory=_factory(be), route_audit=rec, route_id=route_id)

    assert be.calls == []  # never dispatched for this execute() call


def test_route_audit_none_replay_still_redispatches_every_time():
    # No-hook path unchanged: with route_audit=None, no claim occurs at all
    # (claimed=True unconditionally) — dispatch proceeds normally EVERY call, so
    # a caller retrying the SAME route_id without a sink dispatches the backend
    # every time, exactly as before this fix (a None sink means NO idempotency —
    # the compat path stays byte-for-byte unchanged).
    be = ScriptedBackend({})
    chain = _chain(_free_candidate("qwen.qwen3.5-122b"))
    route_id = "no-hook-route"

    result1 = execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                      backend_factory=_factory(be), route_id=route_id)
    result2 = execute(chain, MSG, options=ExecutionOptions(max_tokens=64),
                      backend_factory=_factory(be), route_id=route_id)

    assert result1.response is not None and result2.response is not None
    assert len(be.calls) == 2  # BOTH calls dispatched — no idempotency without a sink
