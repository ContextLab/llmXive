"""T027 — real-call: every successful fill carries resolvable provenance + value in source text.

Gated by LLMXIVE_REAL_TESTS=1.  Uses DartmouthBackend + real network.

SC-002: filled value must be literally present in the fetched source text.
Assertions:
  - provenance.url is non-empty and starts with https://
  - provenance.quote is non-empty
  - provenance.value matches result.value
  - provenance.quote contains provenance.value (value is in the fetched source text)
"""

from __future__ import annotations

import os

import pytest

REAL_TESTS = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


def _dartmouth_backend():
    try:
        from llmxive.backends.dartmouth import DartmouthBackend
        from llmxive.credentials import load_dartmouth_key
        key = load_dartmouth_key()
        if not key:
            return None
        return DartmouthBackend()
    except Exception:
        return None


def _make_numeric_claim(raw: str, resolved_value: str | None = None):
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, raw, "t027-provenance-real")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="t027-provenance-real",
        artifact_path="test/t027.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


@pytest.mark.skipif(not REAL_TESTS, reason="LLMXIVE_REAL_TESTS not set")
class TestFillProvenanceReal:
    """T027: successful fill carries provenance.url (resolvable) + non-empty quote
    AND the filled value is in the fetched source text (SC-002)."""

    def test_oeis_fill_provenance_complete(self, tmp_path):
        """OEIS fill: provenance has url, quote, and value is in the quote."""
        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        from llmxive.fill.service import fill_claim

        claim = _make_numeric_claim(
            "there are 27635 prime knots at 13 crossings (A002863)",
            resolved_value="27635",
        )
        result = fill_claim(
            claim,
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )

        assert result.status == "filled", (
            f"Expected filled, got blocked: {result.reason!r}"
        )
        prov = result.provenance
        assert prov is not None

        # SC-002: provenance.url is resolvable (non-empty https:// URL)
        assert prov.url, "provenance.url must be non-empty"
        assert prov.url.startswith("https://"), (
            f"provenance.url must be a resolvable https:// URL, got {prov.url!r}"
        )

        # SC-002: provenance.quote is non-empty
        assert prov.quote, "provenance.quote must be non-empty"

        # SC-002: provenance.value matches result.value
        assert prov.value == result.value, (
            f"provenance.value {prov.value!r} != result.value {result.value!r}"
        )

        # SC-002: the filled value is literally in the quote
        # (the quote is extracted from the fetched source text, so if the value
        # is in the quote, it was in the source text)
        from llmxive.grounding.service import number_substantiated
        assert number_substantiated(prov.value, prov.quote), (
            f"SC-002 violation: value {prov.value!r} is NOT in provenance.quote {prov.quote!r} "
            "— value must be traceable to the fetched source text"
        )
