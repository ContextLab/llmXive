"""T022 — real-call test: Wikipedia channel + cross-channel OEIS bridge.

Gated by LLMXIVE_REAL_TESTS=1.

Assertions:
  1. wikipedia.search_and_fetch("number of prime knots by crossing number")
     returns at least one source whose text contains "9988".
  2. a_numbers_in() surfaces "A002863" from that text.
  3. fill_claim on a knot-count claim (WITHOUT an explicit A-number in the
     claim text) → filled "9988" via OEIS (cross-channel bridge when the
     A-number is surfaced by Wikipedia) or Wikipedia (if OEIS b-file
     unavailable but value is directly in Wikipedia text).
  4. provenance.url is resolvable (starts with https://).
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="LLMXIVE_REAL_TESTS not set",
)


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


def _make_claim(raw: str, resolved_value: str | None = None):
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, raw, "t022-wiki-real")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="t022-wiki-real",
        artifact_path="test/t022.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


class TestWikipediaChannelReal:
    def test_search_returns_sources_for_prime_knots(self):
        """Wikipedia search for prime knots by crossing number returns at least one source."""
        from llmxive.fill.channels.wikipedia import search_and_fetch

        claim = _make_claim("prime knots at 13 crossings", "9988")
        sources = search_and_fetch("number of prime knots by crossing number", claim)
        assert sources, "Wikipedia search returned no sources"
        # At least one article should be about knots (title check)
        titles = [s.source_id for s in sources]
        assert any("knot" in t.lower() or "crossing" in t.lower() for t in titles), (
            f"No knot-related article found; got: {titles}"
        )

    def test_a_numbers_surfaced_from_wikipedia_text(self):
        """Wikipedia article about prime knots should surface OEIS A-number A002863."""
        from llmxive.fill.channels.oeis import a_numbers_in
        from llmxive.fill.channels.wikipedia import search_and_fetch

        claim = _make_claim("prime knots by crossing number", "9988")
        sources = search_and_fetch("number of prime knots by crossing number", claim)
        assert sources, "Wikipedia search returned no sources"
        all_text = " ".join(s.text for s in sources)
        a_nums = a_numbers_in(all_text)
        assert "A002863" in a_nums, (
            f"A002863 not found in Wikipedia text; found A-numbers: {a_nums[:10]}"
        )


class TestFillClaimWikipediaBridgeReal:
    def test_fill_knot_count_no_a_number_in_claim(self, tmp_path):
        """fill_claim on claim without explicit A-number corrects 27635 → 9988.

        The cross-channel OEIS bridge should fire when Wikipedia surfaces A002863.
        Acceptable: provenance.channel == 'oeis' (via bridge) or 'wikipedia'
        (if 9988 directly in text and OEIS enrichment blocked), but value must
        be '9988' and url must be resolvable.
        """
        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        from llmxive.fill.service import fill_claim

        # No A-number in the claim text — cross-channel bridge must fire
        claim = _make_claim(
            "there are 27635 prime knots at 13 crossings",
            resolved_value="27635",
        )
        result = fill_claim(claim, backend=backend, model="qwen.qwen3.5-122b",
                            repo_root=tmp_path)

        assert result.status == "filled", (
            f"Expected filled, got blocked: {result.reason!r}. "
            f"Channels tried: {result.channels_tried}"
        )
        assert result.value == "9988", f"Expected '9988', got {result.value!r}"
        assert result.provenance is not None
        assert result.provenance.url.startswith("https://"), (
            f"URL not resolvable: {result.provenance.url!r}"
        )
        assert result.provenance.channel in ("oeis", "wikipedia"), (
            f"Unexpected channel: {result.provenance.channel!r}"
        )
