"""T022 — real-call test: fill corrects a wrong superlative (MAGNITUDE claim).

Gated by LLMXIVE_REAL_TESTS=1 and LLMXIVE_CLAIM_FILL=1.

Tests:
1. "the largest planet is Saturn" → VERIFIED with value "Jupiter" from a
   fetched candidate set (wikidata/wikipedia) with provenance.
2. A superlative with no retrievable candidate set → blocked (not falsely filled).

WebFetch-verified fact: Jupiter is the largest planet in the Solar System
(by mass 1.898e27 kg, by volume 1.43e15 km³) — authoritative sources:
  - https://en.wikipedia.org/wiki/Jupiter (confirmed: "largest planet")
  - https://www.wikidata.org/wiki/Q319 (confirmed: largest planet property)
"""

from __future__ import annotations

import os

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="LLMXIVE_REAL_TESTS=1 required",
)


def _make_magnitude_claim(raw: str) -> Claim:
    kind = ClaimKind.MAGNITUDE
    cid = compute_claim_id(kind, raw, "real-call-superlative-test")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="real-call-superlative-test",
        artifact_path="projects/test/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


def _get_backend():
    """Return a real Dartmouth backend, or None if key not available."""
    try:
        from llmxive.credentials import load_dartmouth_key
        key = load_dartmouth_key()
        if not key:
            return None
        from llmxive.backends.dartmouth import DartmouthBackend
        return DartmouthBackend()
    except Exception:
        return None


class TestFillSuperlativeReal:

    def test_wrong_superlative_corrected_to_jupiter(self, tmp_path):
        """fill_claim on a MAGNITUDE claim "the largest planet is Saturn" returns
        "Jupiter" from Wikipedia/wikidata — the fill service corrects the wrong
        extremum from an authoritative sourced candidate set.

        We test fill_claim directly (not the full resolve chain) because
        resolve_superlative's Wikipedia URL heuristic may independently
        ground/refute the claim before fill is reached.  The fill service is
        the authoritative correction layer and is tested here in isolation.

        Jupiter is confirmed as the largest planet in the Solar System:
          https://en.wikipedia.org/wiki/Jupiter — "Jupiter is the largest planet"
          https://www.wikidata.org/wiki/Q319 — largest planet
        """
        backend = _get_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key available")

        os.environ["LLMXIVE_CLAIM_FILL"] = "1"
        try:
            from llmxive.fill.service import fill_claim

            claim = _make_magnitude_claim("the largest planet is Saturn")
            result = fill_claim(
                claim, backend=backend, model=None, repo_root=tmp_path
            )
        finally:
            os.environ.pop("LLMXIVE_CLAIM_FILL", None)

        # Must be FILLED with Jupiter
        assert result.status == "filled", (
            f"Expected fill status 'filled', got {result.status!r}; "
            f"reason: {result.reason}; channels: {result.channels_tried}"
        )
        assert result.value is not None
        assert "jupiter" in result.value.lower(), (
            f"Expected 'Jupiter' in fill value, got {result.value!r}"
        )
        assert result.provenance is not None
        assert result.provenance.channel in ("wikidata", "wikipedia", "paper"), (
            f"Unexpected channel: {result.provenance.channel}"
        )

    def test_unsourceable_superlative_blocked(self, tmp_path):
        """A superlative whose candidate set cannot be sourced stays blocked.

        We test fill_claim directly (not resolve_magnitude) to avoid the
        Wikipedia URL reflection heuristic, which can spuriously ground
        nonsense claims by reflecting the query URL title.  The fill service
        (which uses wikidata/wikipedia/paper channels via structured search)
        must block when no real entity is found for the subject.
        """
        backend = _get_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key available")

        os.environ["LLMXIVE_CLAIM_FILL"] = "1"
        try:
            from llmxive.fill.service import fill_claim

            # Use a fictional category that Wikidata/Wikipedia won't match
            claim = _make_magnitude_claim(
                "the largest Xlqrtbnzian florbnax is Zql"
            )
            result = fill_claim(
                claim, backend=backend, model=None, repo_root=tmp_path
            )
        finally:
            os.environ.pop("LLMXIVE_CLAIM_FILL", None)

        # With a completely fictional entity, fill must stay blocked
        assert result.status == "blocked", (
            f"Expected fill blocked for nonsense superlative, "
            f"got {result.status!r}; value={result.value!r}"
        )
