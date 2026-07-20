"""Slice 1A (spec 026) — the one-candidate execution primitive + the typed
failure-disposition classifier that spec-026 ``execute`` walks a ModelChain over.

The primitive applies the router's per-model safeguards (bounded same-model retry
of generic transients; fail-fast on model-down / reasoning-exhausted / permanent)
but NEVER falls back to another model — that walk belongs to ``execute``. Uses an
injected fake backend (no model mock); ``time.sleep`` is stubbed so the backoff
does not slow the suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from llmxive.backends.base import (
    BackendError,
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    DeadlineExceededError,
    EmptyReplyError,
    ModelDownError,
    PaidGuardDenied,
    PermanentBackendError,
    PricingUnverifiable,
    TransientBackendError,
)
from llmxive.backends.router import (
    CandidateDisposition,
    chat_one_candidate,
    disposition_of,
)

_MSGS = [ChatMessage(role="user", content="ping")]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)


@dataclass
class _Backend:
    """Injected fake: ``raise_map`` maps model -> an exception INSTANCE to raise;
    ``transient_until`` raises a generic transient for the first N calls of a
    model, then succeeds (recovery-on-retry). Every call is recorded."""

    name = "dartmouth"
    raise_map: dict = field(default_factory=dict)  # type: ignore[type-arg]
    transient_until: int = 0
    calls: list = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append(model)
        if self.transient_until and len([c for c in self.calls if c == model]) <= self.transient_until:
            raise TransientBackendError(f"flap {model}")
        exc = self.raise_map.get(model)
        if exc is not None:
            raise exc
        return ChatResponse(text=f"OK from {model}", model=model, backend=self.name)


# ------------------------------ the primitive ------------------------------ #


def test_success_is_a_single_call():
    b = _Backend()
    resp = chat_one_candidate(b, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768)
    assert resp.text == "OK from qwen.qwen3.5-122b"
    assert b.calls == ["qwen.qwen3.5-122b"]  # exactly one call, no fallback


def test_generic_transient_retries_then_raises_same_model_only():
    b = _Backend(raise_map={"m": TransientBackendError("always")})
    with pytest.raises(TransientBackendError):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m", "m", "m"]  # retried 3x, NEVER walked to another model


def test_generic_transient_recovers_on_retry():
    b = _Backend(transient_until=2)  # fail attempts 1+2, succeed on attempt 3
    resp = chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert resp.text == "OK from m"
    assert b.calls == ["m", "m", "m"]


def test_model_down_fails_fast_no_retry():
    b = _Backend(raise_map={"m": ModelDownError("302 outage")})
    with pytest.raises(ModelDownError):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]  # retrying a down model is futile → single call


def test_deadline_exceeded_fails_fast():
    b = _Backend(raise_map={"m": DeadlineExceededError("hung 360s")})
    with pytest.raises(DeadlineExceededError):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]


def test_reasoning_budget_exhausted_fails_fast():
    b = _Backend(raise_map={"m": TransientBackendError("reasoning budget exhausted")})
    with pytest.raises(TransientBackendError):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]  # will re-exhaust → do not burn retries


def test_paid_guard_denied_fails_fast():
    b = _Backend(raise_map={"m": PaidGuardDenied("Dartmouth: opt-in off")})
    with pytest.raises(PaidGuardDenied):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]


def test_permanent_fails_fast():
    b = _Backend(raise_map={"m": PermanentBackendError("bad request")})
    with pytest.raises(PermanentBackendError):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]


def test_backend_unavailable_fails_fast():
    b = _Backend(raise_map={"m": BackendUnavailable("breaker open")})
    with pytest.raises(BackendUnavailable):
        chat_one_candidate(b, _MSGS, model="m", retries=3)
    assert b.calls == ["m"]


def test_model_none_is_single_degrading_call():
    b = _Backend()
    resp = chat_one_candidate(b, _MSGS, model=None)
    assert resp.text == "OK from None"
    assert b.calls == [None]


# --------------------------- disposition classifier ------------------------ #


@pytest.mark.parametrize(
    "exc,expected",
    [
        (PaidGuardDenied("x"), CandidateDisposition.SKIP),
        (BackendUnavailable("x"), CandidateDisposition.RETRY_ADVANCE),
        (ModelDownError("x"), CandidateDisposition.RETRY_ADVANCE),
        (DeadlineExceededError("x"), CandidateDisposition.RETRY_ADVANCE),
        (EmptyReplyError("x"), CandidateDisposition.RETRY_ADVANCE),
        (PricingUnverifiable("x"), CandidateDisposition.RETRY_ADVANCE),
        (TransientBackendError("x"), CandidateDisposition.RETRY_ADVANCE),
        (PermanentBackendError("x"), CandidateDisposition.ABORT),
        (BackendError("x"), CandidateDisposition.ABORT),
        (ValueError("not a backend error"), CandidateDisposition.ABORT),
    ],
)
def test_disposition_mapping(exc, expected):
    assert disposition_of(exc) is expected


def test_paid_denial_is_skip_not_abort_despite_permanent_base():
    """The whole point of the split: PaidGuardDenied subclasses
    PermanentBackendError (so the legacy walker is unchanged) yet classifies as
    SKIP, not ABORT — checked before its base."""
    assert issubclass(PaidGuardDenied, PermanentBackendError)
    assert disposition_of(PaidGuardDenied("x")) is CandidateDisposition.SKIP
    assert disposition_of(PermanentBackendError("x")) is CandidateDisposition.ABORT


def test_pricing_unverifiable_retry_advances_paid_guard_denied_still_skips():
    """Maintainer-identified defect fix: ``PricingUnverifiable`` (catalog
    unreachable / no fresh LKG — a TRANSIENT availability condition) must
    RETRY_ADVANCE like any other transient, never SKIP like a genuine
    ``PaidGuardDenied`` (a VERIFIED-paid model the credit guard declined).
    Collapsing these into one disposition is exactly the operator-facing
    misdiagnosis ("enable paid opt-in" for what is really "the catalog will
    come back") this split exists to prevent."""
    assert issubclass(PricingUnverifiable, TransientBackendError)
    assert disposition_of(PricingUnverifiable("x")) is CandidateDisposition.RETRY_ADVANCE
    assert disposition_of(PaidGuardDenied("x")) is CandidateDisposition.SKIP
