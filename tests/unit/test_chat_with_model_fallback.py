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
    BackendError,
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    DeadlineExceededError,
    ModelDownError,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.router import (
    REASONING_MAX_TOKENS,
    chat_with_model_fallback,
    reasoning_chat,
)

_MSGS = [ChatMessage(role="user", content="ping")]


@pytest.fixture(autouse=True)
def _controlled_fallback_topology(monkeypatch):
    """Pin a deterministic 3-model fallback chain so these MECHANICS tests are
    independent of the production ``MODEL_FALLBACKS`` (which tracks the live,
    churning Dartmouth catalog). Without this, a model-catalog change silently
    broke every chain-walk assertion here — exactly what happened in 2026-06 when
    the qwen / gemma families were retired and the registry migrated to
    ``openai.gpt-oss-120b``. The walker logic is model-agnostic; pinning the
    topology keeps these tests honest without coupling them to model assignments.
    """
    monkeypatch.setattr(
        "llmxive.backends.router.MODEL_FALLBACKS",
        {
            "openai.gpt-oss-120b": [
                "meta.llama-3.2-11b-vision-instruct",
                "meta.codellama-13b-instruct-hf",
            ]
        },
    )


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
    deadline_models: set[str] = field(default_factory=set)
    down_models: set[str] = field(default_factory=set)
    permanent_models: set[str] = field(default_factory=set)
    unavailable_models: set[str] = field(default_factory=set)
    calls: list[dict] = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append(
            {"model": model, "max_tokens": max_tokens, "temperature": temperature}
        )
        if model in self.unavailable_models:
            raise BackendUnavailable(f"circuit open on {model}")
        if model in self.down_models:
            # The 302→outage maintenance-redirect shape (a non-deadline
            # ModelDownError) — must also fast-fail to the peer.
            raise ModelDownError(
                "302 Moved Temporarily; document has moved to outage.dartmouth.edu"
            )
        if model in self.deadline_models:
            raise DeadlineExceededError(
                f"{model} hung past 360s deadline (no response received)"
            )
        if model in self.transient_models:
            raise TransientBackendError(f"synthetic transient on {model}")
        if model in self.permanent_models:
            raise PermanentBackendError(f"synthetic permanent on {model}")
        return ChatResponse(text=f"OK from {model}", model=model, backend=self.name)


def test_primary_healthy_no_fallback():
    backend = _RecordingBackend()
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK from openai.gpt-oss-120b"
    # Exactly one call — the primary — no peer-model fallback used.
    assert [c["model"] for c in backend.calls] == ["openai.gpt-oss-120b"]
    assert backend.calls[0]["max_tokens"] == 32_768


def test_primary_transient_walks_to_first_peer():
    # Primary always-transient → after 3 retries, walk to the first peer
    # (meta.llama-3.2-11b-vision-instruct per MODEL_FALLBACKS) which succeeds.
    backend = _RecordingBackend(transient_models={"openai.gpt-oss-120b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    models = [c["model"] for c in backend.calls]
    # 3 primary attempts, then the first peer.
    assert models == [
        "openai.gpt-oss-120b",
        "openai.gpt-oss-120b",
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
    ]
    # Reasoning-safe budget carried to the PEER too.
    assert backend.calls[-1]["max_tokens"] == 32_768


def test_primary_deadline_hang_falls_to_peer_after_one_attempt():
    """A full-deadline hang on the primary is a model-down signal: the walk must
    SKIP the remaining same-model attempts (each retry would cost another full
    deadline on a hung model) and fall straight to the first healthy peer."""
    backend = _RecordingBackend(deadline_models={"openai.gpt-oss-120b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    models = [c["model"] for c in backend.calls]
    # ONE primary attempt (not 3), then the first peer.
    assert models == ["openai.gpt-oss-120b", "meta.llama-3.2-11b-vision-instruct"]


def test_all_models_deadline_hang_one_attempt_each_then_error():
    """When every model hangs past its deadline, each is tried exactly ONCE (no
    3x burn on the hung primary), then the exhausted chain raises BackendError."""
    backend = _RecordingBackend(
        deadline_models={
            "openai.gpt-oss-120b",
            "meta.llama-3.2-11b-vision-instruct",
            "meta.codellama-13b-instruct-hf",
        }
    )
    with pytest.raises(BackendError):
        chat_with_model_fallback(
            backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
        )
    models = [c["model"] for c in backend.calls]
    assert models == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
        "meta.codellama-13b-instruct-hf",
    ]


def test_reasoning_budget_exhausted_skips_remaining_primary_retries():
    """A 'reasoning budget exhausted' transient skips same-model retries."""

    @dataclass
    class _BudgetExhausted(_RecordingBackend):
        def chat(self, messages, *, model, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
            self.calls.append({"model": model, "max_tokens": max_tokens})
            if model == "openai.gpt-oss-120b":
                raise TransientBackendError("reasoning budget exhausted")
            return ChatResponse(text=f"OK from {model}", model=model, backend=self.name)

    backend = _BudgetExhausted()
    resp = chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    # Only ONE primary attempt (not 3) before the peer.
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
    ]


def test_permanent_on_primary_aborts_no_peer_walk():
    backend = _RecordingBackend(permanent_models={"openai.gpt-oss-120b"})
    with pytest.raises(PermanentBackendError):
        chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")
    # No peer was tried — a permanent (auth/bad-request) failure won't heal.
    assert [c["model"] for c in backend.calls] == ["openai.gpt-oss-120b"]


def test_all_models_transient_raises_backend_error():
    from llmxive.backends.base import BackendError

    backend = _RecordingBackend(
        transient_models={
            "openai.gpt-oss-120b",
            "meta.llama-3.2-11b-vision-instruct",
            "meta.codellama-13b-instruct-hf",
        }
    )
    with pytest.raises(BackendError):
        chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")
    # Whole chain walked: 3 primary + 1 each peer.
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "openai.gpt-oss-120b",
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
        "meta.codellama-13b-instruct-hf",
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

    backend = _NarrowSig(transient_models={"openai.gpt-oss-120b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK meta.llama-3.2-11b-vision-instruct"
    assert backend.calls[-1] == "meta.llama-3.2-11b-vision-instruct"


def test_primary_unavailable_walks_to_healthy_peer():
    """The core fix: a BackendUnavailable (tripped breaker / model down) on the
    PRIMARY must NOT abort — it walks to the next peer. Here qwen's breaker is
    OPEN (BackendUnavailable) but gpt-oss is healthy, so the panel/reviser still
    gets a real answer from the peer instead of the run aborting."""
    backend = _RecordingBackend(unavailable_models={"openai.gpt-oss-120b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    # Primary's breaker is OPEN so it fails fast (ONE call, no same-model
    # retries), then walks straight to the healthy first peer.
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
    ]
    assert backend.calls[-1]["max_tokens"] == 32_768


def test_peer_unavailable_walks_to_next_peer():
    """A BackendUnavailable on a PEER (not just the primary) also walks onward."""
    backend = _RecordingBackend(
        unavailable_models={"openai.gpt-oss-120b", "meta.llama-3.2-11b-vision-instruct"}
    )
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    # Primary unavailable → first peer unavailable → second peer healthy.
    assert resp.text == "OK from meta.codellama-13b-instruct-hf"
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
        "meta.codellama-13b-instruct-hf",
    ]


def test_all_models_unavailable_raises_backend_unavailable():
    """A TRUE full-endpoint outage (every model in the chain BackendUnavailable)
    must raise BackendUnavailable — NOT the generic BackendError — so the run
    loop's clean-abort-on-BackendUnavailable path still fires (preserving the
    breaker's anti-thrash purpose)."""
    backend = _RecordingBackend(
        unavailable_models={
            "openai.gpt-oss-120b",
            "meta.llama-3.2-11b-vision-instruct",
            "meta.codellama-13b-instruct-hf",
        }
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")
    # Whole chain walked: one fast-fail call per model (no same-model retries).
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
        "meta.codellama-13b-instruct-hf",
    ]


def test_mixed_unavailable_and_transient_all_down_raises_backend_unavailable():
    """If at least one failure in an all-down chain was BackendUnavailable, the
    aggregate is BackendUnavailable (the outage signal dominates) so the run
    loop aborts cleanly rather than treating it as a recoverable BackendError."""
    backend = _RecordingBackend(
        transient_models={"openai.gpt-oss-120b", "meta.codellama-13b-instruct-hf"},
        unavailable_models={"meta.llama-3.2-11b-vision-instruct"},
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")


def test_unavailable_primary_then_permanent_peer_still_aborts():
    """A non-Unavailable permanent failure encountered while walking still ends
    the walk with an error; with an Unavailable somewhere in the chain and no
    healthy peer, the aggregate surfaces (Unavailable wins → clean abort)."""
    backend = _RecordingBackend(
        unavailable_models={"openai.gpt-oss-120b"},
        permanent_models={"meta.llama-3.2-11b-vision-instruct", "meta.codellama-13b-instruct-hf"},
    )
    # Primary unavailable (walk), peers are permanent rejections on NON-primary
    # positions (so they don't re-raise immediately) → chain exhausts. Because an
    # Unavailable occurred, the aggregate is BackendUnavailable.
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _MSGS, model="openai.gpt-oss-120b")


# ---------------------------------------------------------------------------
# 302→outage maintenance redirect (a non-deadline ModelDownError) — fast-fails
# to the peer just like a deadline hang (both are "this model is down").
# ---------------------------------------------------------------------------


def test_primary_302_outage_falls_to_peer_after_one_attempt():
    """A 302→outage.dartmouth.edu redirect is an unambiguous model-down signal:
    skip the remaining same-model attempts (no retrying a model in maintenance)
    and fall straight to the first healthy peer."""
    backend = _RecordingBackend(down_models={"openai.gpt-oss-120b"})
    resp = chat_with_model_fallback(
        backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=32_768
    )
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    # ONE primary attempt (not 3), then the first peer.
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
    ]


# ---------------------------------------------------------------------------
# reasoning_chat — THE central reasoning-call entry point. Every claim / fill /
# grounding / triage / review reasoning call routes through it (the former
# per-module _chat_reasoning_safe copies were deleted). It must apply the full
# policy of chat_with_model_fallback with the reasoning-safe budget by default.
# ---------------------------------------------------------------------------


def test_reasoning_chat_healthy_primary_no_fallback_default_budget():
    backend = _RecordingBackend()
    resp = reasoning_chat(backend, _MSGS, model="openai.gpt-oss-120b")
    assert resp.text == "OK from openai.gpt-oss-120b"
    assert [c["model"] for c in backend.calls] == ["openai.gpt-oss-120b"]
    # Reasoning-safe budget applied by default (the single source of truth).
    assert backend.calls[0]["max_tokens"] == REASONING_MAX_TOKENS == 32_768


def test_reasoning_chat_transient_walks_to_peer_carrying_budget():
    backend = _RecordingBackend(transient_models={"openai.gpt-oss-120b"})
    resp = reasoning_chat(backend, _MSGS, model="openai.gpt-oss-120b")
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    # The reasoning-safe budget reaches the PEER too.
    assert backend.calls[-1]["max_tokens"] == REASONING_MAX_TOKENS


def test_reasoning_chat_explicit_max_tokens_overrides_default():
    """A generation-style caller (e.g. the planner re-call) passes a larger
    budget; reasoning_chat honors it instead of the reasoning default."""
    backend = _RecordingBackend()
    reasoning_chat(backend, _MSGS, model="openai.gpt-oss-120b", max_tokens=131_072)
    assert backend.calls[0]["max_tokens"] == 131_072


def test_reasoning_chat_model_none_single_call_no_fallback():
    """model=None makes a single no-fallback call (the offline / injected-fake
    test shape); no peer walk is attempted."""
    backend = _RecordingBackend()
    reasoning_chat(backend, _MSGS, model=None)
    # Exactly ONE call, model=None, and no peer chain was walked.
    assert [c["model"] for c in backend.calls] == [None]


def test_reasoning_chat_302_outage_falls_to_peer():
    """reasoning_chat inherits the model-down fast-fail: a 302→outage on the
    primary routes to the peer after one attempt."""
    backend = _RecordingBackend(down_models={"openai.gpt-oss-120b"})
    resp = reasoning_chat(backend, _MSGS, model="openai.gpt-oss-120b")
    assert resp.text == "OK from meta.llama-3.2-11b-vision-instruct"
    assert [c["model"] for c in backend.calls] == [
        "openai.gpt-oss-120b",
        "meta.llama-3.2-11b-vision-instruct",
    ]


def test_reasoning_chat_degrades_for_stub_backend():
    """A stub backend whose chat signature omits max_tokens/temperature still
    works — _chat_one_model degrades the kwargs (no per-module wrapper needed)."""

    class _StubBackend:
        name = "stub"

        def __init__(self) -> None:
            self.calls: list[dict] = []

        def chat(self, messages, *, model=None):  # narrow signature
            self.calls.append({"model": model})
            return ChatResponse(text="STUB OK", model=model or "?", backend="stub")

    stub = _StubBackend()
    resp = reasoning_chat(stub, _MSGS, model="openai.gpt-oss-120b")  # type: ignore[arg-type]
    assert resp.text == "STUB OK"
    assert stub.calls  # the call landed despite the narrow signature
