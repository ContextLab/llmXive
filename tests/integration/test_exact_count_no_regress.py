"""T027 — Exact-count no-regress guard (spec 018, SC-002/FR-003).

Asserts that a discrete integer count claim ("9,988 prime knots at 13
crossings") is NEVER mis-routed to "approximate" or "computational" by
verify.mode.select_mode — it must return "exact".

Also asserts that grounding.service.number_substantiated with the exact
string "9988" still passes against a doc containing "9,988" (the unchanged
literal-presence gate, FR-003).

LLMXIVE_CLAIM_FILL=1 is set so the mode router is active, mirroring real
pipeline conditions.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LLMXIVE_CLAIM_FILL", "1")


# ---------------------------------------------------------------------------
# Helpers to build a minimal Claim object without a live registry
# ---------------------------------------------------------------------------

def _make_claim(text: str, kind_str: str = "NUMERIC"):
    """Build a minimal Claim-like object for mode-selection tests."""
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus

    kind = ClaimKind[kind_str]
    return Claim(
        claim_id="test-exact-count",
        kind=kind,
        raw_text=text,
        canonical=text,
        context="",
        artifact_path="projects/PROJ-552/idea/test.md",
        source_type="numeric",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
        source_hash="deadbeef",
    )


# ---------------------------------------------------------------------------
# T027 — mode selector must return "exact" for discrete integer counts
# ---------------------------------------------------------------------------

class TestExactCountModeSelection:
    """SC-002: discrete integer count NEVER routes to approximate/computational."""

    def test_9988_prime_knots_routes_exact(self):
        """'9,988 prime knots at 13 crossings' must select 'exact' mode."""
        from llmxive.verify.mode import select_mode

        claim = _make_claim("there are 9,988 prime knots at 13 crossings")
        mode = select_mode(claim, backend=None)
        assert mode == "exact", (
            f"Expected 'exact' for discrete count claim, got {mode!r}. "
            "SC-002/FR-003: integer discrete counts must never loosen to "
            "approximate or computational."
        )

    def test_27635_prime_knots_routes_exact(self):
        """'27,635 prime knots at 13 crossings' (alternative phrasing) must select 'exact'."""
        from llmxive.verify.mode import select_mode

        claim = _make_claim("the exact count is 27,635 prime knots at 13 crossings")
        mode = select_mode(claim, backend=None)
        assert mode == "exact", (
            f"Expected 'exact' for discrete count claim, got {mode!r}."
        )

    def test_integer_count_never_approximate(self):
        """A bare integer discrete count must not return 'approximate'."""
        from llmxive.verify.mode import select_mode

        for text in [
            "there are 9988 prime knots at 13 crossings",
            "9,988 prime knots",
            "27635 knots",
        ]:
            claim = _make_claim(text)
            mode = select_mode(claim, backend=None)
            assert mode != "approximate", (
                f"Claim {text!r} wrongly routed to 'approximate' (mode={mode!r}). "
                "Integer discrete counts must remain on the exact gate."
            )

    def test_integer_count_never_computational(self):
        """A discrete count referencing external entities must not be computational."""
        from llmxive.verify.mode import select_mode

        claim = _make_claim("there are 9,988 prime knots at 13 crossings")
        mode = select_mode(claim, backend=None)
        assert mode != "computational", (
            f"Claim wrongly routed to 'computational' (mode={mode!r}). "
            "Mixed arithmetic+fact claims must not go to computational (FR-017)."
        )


# ---------------------------------------------------------------------------
# T027 — number_substantiated gate unchanged (FR-003, SC-002)
# ---------------------------------------------------------------------------

class TestNumberSubstantiatedGate:
    """The literal-presence gate (number_substantiated) must still pass '9988'
    against source text that contains the comma-formatted form '9,988'.
    """

    def test_9988_substantiated_in_comma_text(self):
        """number_substantiated('9988', '...9,988...') must return True."""
        from llmxive.grounding.service import number_substantiated

        doc_text = (
            "Hoste, Thistlethwaite and Weeks enumerated 9,988 prime knots "
            "up to 13 crossings in their 1998 paper."
        )
        assert number_substantiated("9988", doc_text), (
            "number_substantiated('9988', doc_text) returned False. "
            "The exact-match gate must pass '9988' when '9,988' appears in the source."
        )

    def test_9988_not_substantiated_in_wrong_text(self):
        """number_substantiated must return False when the number is absent."""
        from llmxive.grounding.service import number_substantiated

        doc_text = "There are 1234 knots at 10 crossings."
        assert not number_substantiated("9988", doc_text), (
            "number_substantiated('9988', doc_text) returned True for a doc "
            "that does not contain 9988 — gate is too permissive."
        )

    def test_none_number_always_passes(self):
        """number_substantiated(None, ...) must return True (gate not applicable)."""
        from llmxive.grounding.service import number_substantiated

        assert number_substantiated(None, "any text"), (
            "number_substantiated(None, ...) must return True (gate not applicable)."
        )
