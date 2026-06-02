"""The LLMReviewer routes its backend call through the SAME-BACKEND peer-model
fallback chain (router.chat_with_model_fallback).

Deterministic routing-logic tests with an INJECTED fake backend (not a model
mock): a transient outage on the primary model walks to a peer; a healthy
primary uses no fallback and behaves exactly as before; the reasoning-safe
``max_tokens`` reaches every model in the chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from llmxive.backends.base import ChatResponse, TransientBackendError
from llmxive.convergence.llm_reviewer import LLMReviewer

_REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_PRIMARY = """\
---
reviewer_name: requirements_coverage
verdict: minor_revision
concerns:
  - severity: requirement
    location: "FR-002"
    text: "FR-002 has no corresponding success criterion (from PRIMARY)"
---
"""

_VALID_PEER = """\
---
reviewer_name: requirements_coverage
verdict: accept
concerns: []
---
"""


@dataclass
class _ModelRoutingBackend:
    """Injected fake: per-model success/failure + records kwargs.

    ``replies`` maps a model id → response text; ``transient_models`` raise
    TransientBackendError so we can prove the reviewer walked to a peer.
    """

    replies: dict[str, str]
    transient_models: set[str] = field(default_factory=set)
    calls: list[dict] = field(default_factory=list)  # type: ignore[type-arg]

    def chat(self, messages, *, model, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append({"model": model, "max_tokens": max_tokens})
        if model in self.transient_models:
            raise TransientBackendError(f"reasoning budget exhausted on {model}")
        return ChatResponse(
            text=self.replies[model], model=model, backend="dartmouth"
        )


def _reviewer(backend) -> LLMReviewer:
    return LLMReviewer(
        lens="requirements_coverage",
        stage="clarified",
        backend=backend,
        repo_root=_REPO_ROOT,
        model="qwen.qwen3.5-122b",
    )


_ARTIFACTS = {"specs/000-x/spec.md": "## Functional Requirements\n- FR-002: do X.\n"}


def test_healthy_primary_no_fallback():
    backend = _ModelRoutingBackend(replies={"qwen.qwen3.5-122b": _VALID_PRIMARY})
    concerns = _reviewer(backend).identify(_ARTIFACTS, constitution=None, advisory=[])
    # Behavior identical to today: the primary's concern is returned.
    assert len(concerns) == 1
    assert "PRIMARY" in concerns[0].text
    # Exactly one call to the primary — no peer-model fallback.
    assert [c["model"] for c in backend.calls] == ["qwen.qwen3.5-122b"]
    # Reasoning-safe default max_tokens (32_768) was passed.
    assert backend.calls[0]["max_tokens"] == 32_768


def test_primary_transient_walks_to_peer():
    backend = _ModelRoutingBackend(
        replies={
            "qwen.qwen3.5-122b": _VALID_PRIMARY,  # never reached (transient)
            "openai.gpt-oss-120b": _VALID_PEER,
        },
        transient_models={"qwen.qwen3.5-122b"},
    )
    concerns = _reviewer(backend).identify(_ARTIFACTS, constitution=None, advisory=[])
    # The PEER's response (accept → no concerns) is what the reviewer returned,
    # proving the fallback chain was walked instead of stalling on the dead model.
    assert concerns == []
    models = [c["model"] for c in backend.calls]
    assert models[-1] == "openai.gpt-oss-120b"
    assert "qwen.qwen3.5-122b" in models
    # The reasoning-safe budget reached the PEER too.
    assert backend.calls[-1]["max_tokens"] == 32_768
