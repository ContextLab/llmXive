"""T033 — Real-call tests for claims/triple.py resolvers.

Gated by LLMXIVE_REAL_TESTS=1.

Tests:
- A TRUE relational claim (well-known capital-of) → VERIFIED or NEI (never REFUTED).
- A FALSE relational claim → REFUTED or NEI (never VERIFIED).
- A TRUE superlative claim (well-known largest object) → VERIFIED or NEI (never REFUTED).
- A FALSE superlative claim → REFUTED or NEI (never VERIFIED).

NOTE on external facts asserted here:
- "Paris is the capital of France" — universally known; no URL needed.
- "Berlin is the capital of France" — universally false.
- "Jupiter is the largest planet in the Solar System" — NASA/IAU standard fact.
  Wikipedia source: https://en.wikipedia.org/wiki/Jupiter (fetched 2026-05-30;
  article confirms Jupiter is the largest planet by mass and volume).
- "Mercury is the largest planet in the Solar System" — false.

If a source cannot be retrieved at runtime the test accepts NEI (blocking path)
rather than failing; the important invariant is that TRUE claims never return
REFUTED and FALSE claims never return VERIFIED.
"""

from __future__ import annotations

import os
import pytest

from llmxive.claims.models import ClaimStatus

_REAL = os.environ.get("LLMXIVE_REAL_TESTS", "").strip().lower() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(not _REAL, reason="LLMXIVE_REAL_TESTS not set")


def _make_backend_model():
    """Return (backend, model) for real calls using the Dartmouth backend.

    DartmouthBackend resolves the API key from env / credentials file via
    _ensure_api_key_env(); no key arg is accepted by the constructor.
    """
    from llmxive.backends.dartmouth import DartmouthBackend

    backend = DartmouthBackend()
    model = "qwen.qwen3.5-122b"
    return backend, model


def _repo_root():
    from llmxive.config import repo_root
    return repo_root()


# ---------------------------------------------------------------------------
# Relational claims
# ---------------------------------------------------------------------------

class TestRelationalReal:
    def test_true_capital_of(self):
        """Paris is the capital of France → VERIFIED or NEI (never REFUTED)."""
        from llmxive.claims.triple import resolve_relational

        backend, model = _make_backend_model()
        verdict = resolve_relational(
            "Paris is the capital of France",
            backend=backend, model=model, repo_root=_repo_root(),
        )
        assert verdict.status != ClaimStatus.REFUTED, (
            f"True claim incorrectly REFUTED: {verdict}"
        )
        assert verdict.status in (ClaimStatus.VERIFIED, ClaimStatus.NOT_ENOUGH_INFO)

    def test_false_capital_of(self):
        """Berlin is the capital of France → REFUTED or NEI (never VERIFIED)."""
        from llmxive.claims.triple import resolve_relational

        backend, model = _make_backend_model()
        verdict = resolve_relational(
            "Berlin is the capital of France",
            backend=backend, model=model, repo_root=_repo_root(),
        )
        assert verdict.status != ClaimStatus.VERIFIED, (
            f"False claim incorrectly VERIFIED: {verdict}"
        )
        assert verdict.status in (ClaimStatus.REFUTED, ClaimStatus.NOT_ENOUGH_INFO)


# ---------------------------------------------------------------------------
# Superlative claims
# ---------------------------------------------------------------------------

class TestSuperlativeReal:
    def test_true_largest_planet(self):
        """Jupiter is the largest planet in the Solar System → VERIFIED or NEI."""
        from llmxive.claims.triple import resolve_superlative

        backend, model = _make_backend_model()
        verdict = resolve_superlative(
            "Jupiter is the largest planet in the Solar System",
            backend=backend, model=model, repo_root=_repo_root(),
        )
        assert verdict.status != ClaimStatus.REFUTED, (
            f"True superlative incorrectly REFUTED: {verdict}"
        )
        assert verdict.status in (ClaimStatus.VERIFIED, ClaimStatus.NOT_ENOUGH_INFO)

    def test_false_largest_planet(self):
        """Mercury is the largest planet in the Solar System → REFUTED or NEI."""
        from llmxive.claims.triple import resolve_superlative

        backend, model = _make_backend_model()
        verdict = resolve_superlative(
            "Mercury is the largest planet in the Solar System",
            backend=backend, model=model, repo_root=_repo_root(),
        )
        assert verdict.status != ClaimStatus.VERIFIED, (
            f"False superlative incorrectly VERIFIED: {verdict}"
        )
        assert verdict.status in (ClaimStatus.REFUTED, ClaimStatus.NOT_ENOUGH_INFO)
