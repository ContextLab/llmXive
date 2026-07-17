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
