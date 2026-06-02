"""Unit tests for :func:`router.chat_with_model_fallback` — the SAME-BACKEND
peer-model fallback walk used by the convergence panel + reviser.

These exercise the routing/parallelism LOGIC with an INJECTED fake backend
(not a model mock): the fake's ``chat`` decides success/failure per model so we
can deterministically assert which peer the chain landed on, that the
reasoning-safe ``max_tokens`` is carried to every peer, and that a healthy
primary never triggers a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from llmxive.backends.base import (
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.router import chat_with_model_fallback

_MSGS = [ChatMessage(role="user", content="ping")]


@dataclass
class _RecordingBackend:
    """Injected fake backend (no model mock).

    ``transient_models`` raise ``TransientBackendError`` on every call;
    ``permanent_models`` raise ``PermanentBackendError``; ``unavailable_models``
    raise ``BackendUnavailable`` (a tripped circuit breaker / model-down signal);
    any other model returns a ``ChatResponse`` naming the model that answered.
    Every call is recorded so tests can assert the walked chain + the kwargs
    passed.
    """

    name = "dartmouth"
    transient_models: set[str] = field(default_factory=set)
    permanent_models: set[str] = field(default_factory=set)
    unavailable_models: set[str] = field(default_factory=set)
    calls: list[dict] = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, *, model, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append(
            {"model": model, "max_tokens": max_tokens, "temperature": temperature}
        )
        if model in self.unavailable_models:
            raise BackendUnavailable(f"circuit open on {model}")
        if model in self.transient_models:
            raise TransientBackendError(f"synthetic transient on {model}")
        if model in self.permanent_models:
            raise PermanentBackendError(f"synthetic permanent on {model}")
        return ChatResponse(text=f"OK from {model}", model=model, backend=self.name)


def test_primary_healthy_no_fallback():
    backend = _RecordingBackend()
    resp = chat_with_model_fallback(
        backend, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768
    )
    assert resp.text == "OK from qwen.qwen3.5-122b"
    # Exactly one call — the primary — no peer-model fallback used.
    assert [c["model"] for c in backend.calls] == ["qwen.qwen3.5-122b"]
    assert backend.calls[0]["max_tokens"] == 32_768


def test_primary_transient_walks_to_first_peer():
    # Primary always-transient → after 3 retries, walk to the first peer
    # (openai.gpt-oss-120b per MODEL_FALLBACKS) which succeeds.
    backend = _RecordingBackend(transient_models={"qwen.qwen3.5-122b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768
    )
    assert resp.text == "OK from openai.gpt-oss-120b"
    models = [c["model"] for c in backend.calls]
    # 3 primary attempts, then the first peer.
    assert models == [
        "qwen.qwen3.5-122b",
        "qwen.qwen3.5-122b",
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
    ]
    # Reasoning-safe budget carried to the PEER too.
    assert backend.calls[-1]["max_tokens"] == 32_768


def test_reasoning_budget_exhausted_skips_remaining_primary_retries():
    """A 'reasoning budget exhausted' transient skips same-model retries."""

    @dataclass
    class _BudgetExhausted(_RecordingBackend):
        def chat(self, messages, *, model, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
            self.calls.append({"model": model, "max_tokens": max_tokens})
            if model == "qwen.qwen3.5-122b":
                raise TransientBackendError("reasoning budget exhausted")
            return ChatResponse(text=f"OK from {model}", model=model, backend=self.name)

    backend = _BudgetExhausted()
    resp = chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")
    assert resp.text == "OK from openai.gpt-oss-120b"
    # Only ONE primary attempt (not 3) before the peer.
    assert [c["model"] for c in backend.calls] == [
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
    ]


def test_permanent_on_primary_aborts_no_peer_walk():
    backend = _RecordingBackend(permanent_models={"qwen.qwen3.5-122b"})
    with pytest.raises(PermanentBackendError):
        chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")
    # No peer was tried — a permanent (auth/bad-request) failure won't heal.
    assert [c["model"] for c in backend.calls] == ["qwen.qwen3.5-122b"]


def test_all_models_transient_raises_backend_error():
    from llmxive.backends.base import BackendError

    backend = _RecordingBackend(
        transient_models={
            "qwen.qwen3.5-122b",
            "openai.gpt-oss-120b",
            "google.gemma-4-31B-it",
        }
    )
    with pytest.raises(BackendError):
        chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")
    # Whole chain walked: 3 primary + 1 each peer.
    assert [c["model"] for c in backend.calls] == [
        "qwen.qwen3.5-122b",
        "qwen.qwen3.5-122b",
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
        "google.gemma-4-31B-it",
    ]


def test_model_none_single_call_no_chain():
    """``model=None`` (offline reviser shape) → exactly one chat, no chain."""

    @dataclass
    class _NoModelKwarg:
        name = "fake"
        calls: list = field(default_factory=list)  # type: ignore[type-arg]

        def chat(self, messages, model=None):  # narrower signature, no max_tokens
            self.calls.append(model)
            return ChatResponse(text="OK", model="fake", backend="fake")

    backend = _NoModelKwarg()
    resp = chat_with_model_fallback(backend, _MSGS, model=None, max_tokens=32_768)
    assert resp.text == "OK"
    assert backend.calls == [None]  # one call, no peer fallback


def test_kwarg_degradation_for_narrow_signature():
    """A fake whose ``chat`` omits ``max_tokens`` still works (TypeError
    degradation), and the peer-model chain is still walked on transient."""

    @dataclass
    class _NarrowSig:
        name = "fake"
        transient_models: set = field(default_factory=set)  # type: ignore[type-arg]
        calls: list = field(default_factory=list)  # type: ignore[type-arg]

        def chat(self, messages, model=None):  # no max_tokens kwarg
            self.calls.append(model)
            if model in self.transient_models:
                raise TransientBackendError(f"transient {model}")
            return ChatResponse(text=f"OK {model}", model=model or "?", backend="fake")

    backend = _NarrowSig(transient_models={"qwen.qwen3.5-122b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768
    )
    assert resp.text == "OK openai.gpt-oss-120b"
    assert backend.calls[-1] == "openai.gpt-oss-120b"


def test_primary_unavailable_walks_to_healthy_peer():
    """The core fix: a BackendUnavailable (tripped breaker / model down) on the
    PRIMARY must NOT abort — it walks to the next peer. Here qwen's breaker is
    OPEN (BackendUnavailable) but gpt-oss is healthy, so the panel/reviser still
    gets a real answer from the peer instead of the run aborting."""
    backend = _RecordingBackend(unavailable_models={"qwen.qwen3.5-122b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768
    )
    assert resp.text == "OK from openai.gpt-oss-120b"
    # Primary's breaker is OPEN so it fails fast (ONE call, no same-model
    # retries), then walks straight to the healthy first peer.
    assert [c["model"] for c in backend.calls] == [
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
    ]
    assert backend.calls[-1]["max_tokens"] == 32_768


def test_peer_unavailable_walks_to_next_peer():
    """A BackendUnavailable on a PEER (not just the primary) also walks onward."""
    backend = _RecordingBackend(
        unavailable_models={"qwen.qwen3.5-122b", "openai.gpt-oss-120b"}
    )
    resp = chat_with_model_fallback(
        backend, _MSGS, model="qwen.qwen3.5-122b", max_tokens=32_768
    )
    # Primary unavailable → first peer unavailable → second peer healthy.
    assert resp.text == "OK from google.gemma-4-31B-it"
    assert [c["model"] for c in backend.calls] == [
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
        "google.gemma-4-31B-it",
    ]


def test_all_models_unavailable_raises_backend_unavailable():
    """A TRUE full-endpoint outage (every model in the chain BackendUnavailable)
    must raise BackendUnavailable — NOT the generic BackendError — so the run
    loop's clean-abort-on-BackendUnavailable path still fires (preserving the
    breaker's anti-thrash purpose)."""
    backend = _RecordingBackend(
        unavailable_models={
            "qwen.qwen3.5-122b",
            "openai.gpt-oss-120b",
            "google.gemma-4-31B-it",
        }
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")
    # Whole chain walked: one fast-fail call per model (no same-model retries).
    assert [c["model"] for c in backend.calls] == [
        "qwen.qwen3.5-122b",
        "openai.gpt-oss-120b",
        "google.gemma-4-31B-it",
    ]


def test_mixed_unavailable_and_transient_all_down_raises_backend_unavailable():
    """If at least one failure in an all-down chain was BackendUnavailable, the
    aggregate is BackendUnavailable (the outage signal dominates) so the run
    loop aborts cleanly rather than treating it as a recoverable BackendError."""
    backend = _RecordingBackend(
        transient_models={"qwen.qwen3.5-122b", "google.gemma-4-31B-it"},
        unavailable_models={"openai.gpt-oss-120b"},
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")


def test_unavailable_primary_then_permanent_peer_still_aborts():
    """A non-Unavailable permanent failure encountered while walking still ends
    the walk with an error; with an Unavailable somewhere in the chain and no
    healthy peer, the aggregate surfaces (Unavailable wins → clean abort)."""
    backend = _RecordingBackend(
        unavailable_models={"qwen.qwen3.5-122b"},
        permanent_models={"openai.gpt-oss-120b", "google.gemma-4-31B-it"},
    )
    # Primary unavailable (walk), peers are permanent rejections on NON-primary
    # positions (so they don't re-raise immediately) → chain exhausts. Because an
    # Unavailable occurred, the aggregate is BackendUnavailable.
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="qwen.qwen3.5-122b")
