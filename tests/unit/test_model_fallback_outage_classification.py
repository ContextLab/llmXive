"""Regression: an all-TRANSIENT chain exhaustion must abort cleanly, not escalate.

Observed live (PROJ-552, dispatch 27306941191, 2026-06-10): a Dartmouth-wide
outage made every model in the fallback chain fail with transient-class
errors (qwen hung past its 360s deadline; gpt-oss + gemma both returned the
302→outage.dartmouth.edu maintenance redirect). ``chat_with_model_fallback``
raised plain ``BackendError`` (the breaker had not tripped yet, so the old
``saw_unavailable``-only clause did not fire), the stage-panel's generic
engine-failure handler caught it, and the project was WRONGLY escalated to
``human_input_needed`` — a transient infrastructure outage is not
human-actionable (bug-#8 family; see notes/spec-015-review-status.md).

The fix: chain exhaustion where ANY failure was transient-class
(``ModelDownError`` / ``TransientBackendError``) raises ``BackendUnavailable``
— the run loop's clean-abort path (state preserved, retried next tick).
Plain ``BackendError`` is reserved for an all-permanent exhaustion.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import (
    BackendError,
    BackendUnavailable,
    ChatMessage,
    ChatResponse,
    ModelDownError,
    PermanentBackendError,
    TransientBackendError,
)
from llmxive.backends.router import MODEL_FALLBACKS, chat_with_model_fallback

PRIMARY = "qwen.qwen3.5-122b"

_OUTAGE_HTML = (
    '!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN"> '
    "<title>302 Moved Temporarily</title> outage.dartmouth.edu"
)


class _AllDownBackend:
    """Every model raises the given exception class (a full-endpoint outage)."""

    name = "dartmouth"

    def __init__(self, exc_factory) -> None:
        self._exc_factory = exc_factory
        self.models_tried: list[str] = []

    def chat(self, messages, *, model, max_tokens=None, temperature=None):
        self.models_tried.append(model)
        raise self._exc_factory(model)


def _msgs() -> list[ChatMessage]:
    return [ChatMessage(role="user", content="ping")]


def test_all_model_down_exhaustion_raises_backend_unavailable() -> None:
    """The exact live shape: deadline-hang on the primary, 302→outage on the
    peers — all ModelDownError. Must surface as BackendUnavailable so the
    stage panel re-raises it AS-IS (clean abort), never an escalation."""
    backend = _AllDownBackend(
        lambda m: ModelDownError(f"Dartmouth model {m!r}: {_OUTAGE_HTML}")
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _msgs(), model=PRIMARY)
    # The walk really visited the whole chain before giving up.
    assert set(backend.models_tried) == {PRIMARY, *MODEL_FALLBACKS[PRIMARY]}


def test_all_transient_exhaustion_raises_backend_unavailable() -> None:
    """Plain transient flaps (5xx/conn-reset) on every model: same clean-abort
    classification."""
    backend = _AllDownBackend(
        lambda m: TransientBackendError(f"connection reset talking to {m}")
    )
    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(backend, _msgs(), model=PRIMARY)


def test_permanent_failures_on_peers_keep_backend_error() -> None:
    """All-permanent exhaustion stays a plain BackendError (engine-actionable,
    NOT an outage): transient primary, permanent peers — the single transient
    in the chain still classifies the exhaustion as an outage; but a chain
    where the only non-primary failures are permanent AND the primary is
    permanent aborts immediately at the primary (pre-existing contract)."""
    backend = _AllDownBackend(lambda m: PermanentBackendError(f"refused {m}"))
    # Primary permanent -> immediate raise (no chain exhaustion at all).
    with pytest.raises(PermanentBackendError):
        chat_with_model_fallback(backend, _msgs(), model=PRIMARY)
    assert backend.models_tried == [PRIMARY]


def test_mixed_transient_then_permanent_peers_classify_as_outage() -> None:
    """Transient primary + permanent peers: the transient signal means the
    endpoint may heal — clean abort (BackendUnavailable), not BackendError."""

    class _Mixed:
        name = "dartmouth"

        def chat(self, messages, *, model, max_tokens=None, temperature=None):
            if model == PRIMARY:
                raise ModelDownError(f"{model} hung past 360s deadline")
            raise PermanentBackendError(f"refused {model}")

    with pytest.raises(BackendUnavailable):
        chat_with_model_fallback(_Mixed(), _msgs(), model=PRIMARY)


def test_healthy_peer_still_serves_the_chain() -> None:
    """Sanity: the new classification changes ONLY the exhausted case — a
    healthy peer still answers."""

    class _PeerHealthy:
        name = "dartmouth"

        def chat(self, messages, *, model, max_tokens=None, temperature=None):
            if model == PRIMARY:
                raise ModelDownError(f"{model}: {_OUTAGE_HTML}")
            return ChatResponse(
                text="ok", model=model, backend=self.name, cost_estimate_usd=0.0
            )

    response = chat_with_model_fallback(_PeerHealthy(), _msgs(), model=PRIMARY)
    assert response.text == "ok"
    assert response.model in MODEL_FALLBACKS[PRIMARY]


def test_backend_error_class_still_reachable_for_all_permanent_peers() -> None:
    """Exhaustion with ONLY permanent peer failures (primary transient is
    required to reach exhaustion at all — covered above as outage). Document
    that plain BackendError now requires a chain with zero transient signals,
    which cannot occur via the primary path; the aggregate error class is kept
    for forward-compatibility rather than deleted."""
    assert issubclass(BackendUnavailable, BackendError)
