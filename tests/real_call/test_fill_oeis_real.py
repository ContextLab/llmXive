"""T021 — real-call test: OEIS channel + fill_claim on A002863.

Gated by LLMXIVE_REAL_TESTS=1.

Assertions:
  1. oeis.fetch_bfile("A002863")[13] == 9988  (verified OEIS b-file lookup)
  2. fill_claim on a claim whose text mentions A002863 at 13 crossings returns
     a FillResult with status="filled", value="9988", channel="oeis", and a
     resolvable url (https://oeis.org/A002863).
  3. "9988" appears in provenance.quote.
"""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="LLMXIVE_REAL_TESTS not set",
)


def _dartmouth_backend():
    """Return a real Dartmouth backend, or None if no key is configured."""
    try:
        from llmxive.backends.dartmouth import DartmouthBackend
        from llmxive.credentials import load_dartmouth_key
        key = load_dartmouth_key()
        if not key:
            return None
        return DartmouthBackend()
    except Exception:
        return None


def _make_claim(raw: str, resolved_value: str | None = None):
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, raw, "t021-oeis-real")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="t021-oeis-real",
        artifact_path="test/t021.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


class TestOeisRealBfile:
    def test_fetch_bfile_a002863_index_13(self):
        """Directly verify the known OEIS b-file value: A002863[13] == 9988."""
        from llmxive.fill.channels.oeis import fetch_bfile
        data = fetch_bfile("A002863")
        assert data, "fetch_bfile returned empty dict — check network/OEIS availability"
        assert 13 in data, f"index 13 not in b-file; available keys sample: {sorted(data.keys())[:20]}"
        assert data[13] == 9988, f"A002863[13] expected 9988, got {data[13]}"


class TestFillClaimOeisReal:
    def test_fill_claim_a002863_via_direct_mention(self, tmp_path):
        """fill_claim on a claim mentioning A002863 at 13 crossings → filled "9988"."""
        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        from llmxive.fill.service import fill_claim

        claim = _make_claim(
            "there are 27635 prime knots at 13 crossings (A002863)",
            resolved_value="27635",
        )
        result = fill_claim(claim, backend=backend, model="qwen.qwen3.5-122b",
                            repo_root=tmp_path)

        assert result.status == "filled", (
            f"Expected filled, got blocked: {result.reason!r}"
        )
        assert result.value == "9988", f"Expected value '9988', got {result.value!r}"
        assert result.provenance is not None
        assert result.provenance.channel == "oeis", (
            f"Expected channel 'oeis', got {result.provenance.channel!r}"
        )
        assert result.provenance.url.startswith("https://oeis.org/"), (
            f"URL not resolvable: {result.provenance.url!r}"
        )
        assert "9988" in result.provenance.quote, (
            f"'9988' not in provenance.quote: {result.provenance.quote!r}"
        )
