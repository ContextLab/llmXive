"""Spec 020 T005 — strip/smooth transform (C3 contract; FR-002a/b/c, SC-001/001a).

Offline. Uses a deterministic in-test backend (a real object whose ``chat``
returns canned text — NOT unittest.mock) to exercise the real re-detect guard +
deterministic fallback logic. The actual LLM rewrite quality is covered by the
real-call integration test (T007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llmxive.backends.base import ChatResponse
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.claims.smooth import strip_and_smooth


@dataclass
class _ScriptedBackend:
    """Returns a fixed rewrite for every chat; records calls. No model mock."""

    reply: str
    name: str = "dartmouth"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append({"model": model})
        return ChatResponse(text=self.reply, model=model or "m", backend=self.name)


def _numeric_claim(raw_text: str, canonical: str | None = None) -> Claim:
    canonical = canonical or raw_text
    return Claim(
        claim_id=compute_claim_id(ClaimKind.NUMERIC, canonical, ""),
        kind=ClaimKind.NUMERIC,
        raw_text=raw_text,
        canonical=canonical,
        context="",
        artifact_path="projects/PROJ-x/specs/plan.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="",
    )


PASSAGE = "There are exactly 49 prime knots at 13 crossings (Rolfsen 1976)."


def test_llm_rewrite_accepted_when_value_removed() -> None:
    # The rewrite drops the specific count → guard passes, rewrite is returned.
    backend = _ScriptedBackend(
        reply="The number of prime knots grows with crossing number (Rolfsen 1976)."
    )
    claim = _numeric_claim(PASSAGE)
    out = strip_and_smooth(PASSAGE, claim, backend=backend, model=None)
    assert "49" not in out
    assert "Rolfsen 1976" in out  # citation preserved (FR-002c)
    assert backend.calls  # the LLM was consulted


def test_deterministic_fallback_when_rewrite_still_asserts() -> None:
    # The model "rewrite" still contains 49 → guard fails → deterministic fallback
    # excises the value, guaranteeing claim-free output (FR-002a).
    backend = _ScriptedBackend(reply="There are still exactly 49 prime knots here.")
    claim = _numeric_claim(PASSAGE)
    out = strip_and_smooth(PASSAGE, claim, backend=backend, model=None)
    assert "49" not in out
    assert "Rolfsen 1976" in out  # citation preserved by the fallback (FR-002c)
    assert "prime knots" in out  # surrounding content preserved


def test_fallback_used_when_backend_unavailable() -> None:
    # No backend → straight to deterministic fallback; still claim-free.
    claim = _numeric_claim(PASSAGE)
    out = strip_and_smooth(PASSAGE, claim, backend=None, model=None)
    assert "49" not in out
    assert "13" in out  # qualifier number (crossing index) is NOT stripped
    assert "Rolfsen 1976" in out


def test_idempotent_on_already_smoothed_text() -> None:
    # SC-001a: re-running on a passage with no specific value is a no-op.
    smoothed = "The number of prime knots grows with crossing number (Rolfsen 1976)."
    claim = _numeric_claim(PASSAGE)  # original claim (asserts 49)
    backend = _ScriptedBackend(reply="SHOULD NOT BE CALLED")
    once = strip_and_smooth(smoothed, claim, backend=backend, model=None)
    assert once == smoothed  # unchanged
    assert not backend.calls  # no LLM call — nothing to strip (idempotent no-op)
    twice = strip_and_smooth(once, claim, backend=backend, model=None)
    assert twice == once


def test_only_asserted_value_removed_qualifier_kept() -> None:
    # FR-002c: the qualifier number (13 crossings) survives; only 49 is stripped.
    claim = _numeric_claim(PASSAGE)
    out = strip_and_smooth(PASSAGE, claim, backend=None, model=None)
    assert "49" not in out
    assert "13" in out
