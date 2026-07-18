"""Review finding 3: a SELECTED-but-unusable local fallback must ADVANCE the
model chain (so a later guarded paid candidate is still reached), NOT abort it.

``LocalBackend`` is a first-class candidate in the spec-026 composite snapshot, so
when its optional runtime (transformers) or checkpoint cannot load, that has to be
a backend-UNAVAILABLE outcome (``disposition_of`` → RETRY_ADVANCE) rather than a
request-level ``PermanentBackendError`` (→ ABORT), which would strand the chain on
the local model before Claude.
"""

from __future__ import annotations

import sys

import pytest

from llmxive.backends.base import BackendUnavailable, ChatMessage, PermanentBackendError
from llmxive.backends.local import LocalBackend
from llmxive.backends.router import CandidateDisposition, disposition_of

_LOCAL_MODEL = "Qwen/Qwen2.5-3B-Instruct"
_MSGS = [ChatMessage(role="user", content="hi")]


def test_missing_transformers_is_backend_unavailable_not_permanent(monkeypatch):
    # Force `from transformers import ...` to fail (a None entry in sys.modules
    # makes the import raise ImportError), simulating a runner without the heavy
    # optional dependency installed.
    monkeypatch.setitem(sys.modules, "transformers", None)

    with pytest.raises(BackendUnavailable):
        LocalBackend().chat(_MSGS, model=_LOCAL_MODEL)


def test_missing_transformers_classifies_as_advance(monkeypatch):
    monkeypatch.setitem(sys.modules, "transformers", None)
    try:
        LocalBackend().chat(_MSGS, model=_LOCAL_MODEL)
    except Exception as exc:  # noqa: BLE001 — we assert the classification below
        assert isinstance(exc, PermanentBackendError)  # still a permanent-family error…
        assert disposition_of(exc) is CandidateDisposition.RETRY_ADVANCE  # …but ADVANCES
    else:  # pragma: no cover - must raise
        pytest.fail("expected BackendUnavailable when transformers is unavailable")
