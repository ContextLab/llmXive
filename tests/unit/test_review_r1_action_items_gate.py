"""R1 action-items gate (the single shared review protocol).

A reviewer that requests revision but enumerates ZERO concerns is
self-contradictory — it says "change this" with nothing to act on. The shared
LLMReviewer.identify path REJECTS such a review and RESUBMITS it once with an
explicit instruction; a genuine clean accept (verdict: accept, no concerns) is
NOT re-prompted. This guarantees every round-1 non-accept carries the action
items round 2 addresses and round 3 signs off on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.convergence.llm_reviewer import LLMReviewer

# Real repo root so the per-lens panel prompt loads (same as the other
# llm_reviewer tests). The review cache is disabled per-test so the injected
# backend is actually called.
_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _SeqBackend:
    """Returns queued responses in call order; records the models called."""

    responses: list[str]
    calls: list[str] = field(default_factory=list)

    def chat(self, messages, *, model, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append(model)
        idx = min(len(self.calls) - 1, len(self.responses) - 1)
        return ChatResponse(text=self.responses[idx], model=model, backend="dartmouth")


_ART = {"specs/000-x/spec.md": "## Functional Requirements\n- FR-001: do X.\n"}


@pytest.fixture(autouse=True)
def _no_cache(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE", "0")


def _reviewer(backend) -> LLMReviewer:
    return LLMReviewer(
        lens="requirements_coverage",
        stage="clarified",
        backend=backend,
        repo_root=_REPO_ROOT,
        model="openai.gpt-oss-120b",
    )


def test_nonaccept_with_zero_concerns_is_rejected_and_resubmitted():
    bad = "---\nverdict: major_revision\nconcerns: []\n---\n"
    good = (
        "---\nverdict: major_revision\nconcerns:\n"
        "  - severity: requirement\n    text: FR-001 lacks an acceptance test\n---\n"
    )
    backend = _SeqBackend(responses=[bad, good])
    concerns = _reviewer(backend).identify(_ART, constitution=None, advisory=[])
    assert len(backend.calls) == 2  # rejected + resubmitted exactly once
    assert len(concerns) == 1
    assert "acceptance test" in concerns[0].text


def test_clean_accept_with_zero_concerns_is_not_resubmitted():
    accept = "---\nverdict: accept\nconcerns: []\n---\n"
    backend = _SeqBackend(responses=[accept])
    concerns = _reviewer(backend).identify(_ART, constitution=None, advisory=[])
    assert len(backend.calls) == 1  # genuine accept -> no resubmit
    assert concerns == []
