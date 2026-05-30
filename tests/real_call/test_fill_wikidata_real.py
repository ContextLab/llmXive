"""T031 — US3 real-call: entity/Wikidata fill corrects a wrong entity claim.

Gated by LLMXIVE_REAL_TESTS=1.  Uses DartmouthBackend + real network.

Test case: "The capital of Australia is Sydney" — wrong; correct is Canberra.
(Verified fact: Canberra is the capital of Australia, not Sydney.)

Assertions:
  1. fill_claim corrects the claim to "Canberra" (or a value containing it)
     with Wikidata or Wikipedia provenance.
  2. The filled value is literally present in the fetched source text.
  3. A RELATIONAL or MAGNITUDE claim → fill_claim returns blocked (deferred v1).
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


def _make_claim(kind, raw: str, resolved_value: str | None = None):
    from llmxive.claims.models import Claim, ClaimStatus, compute_claim_id
    cid = compute_claim_id(kind, raw, "t031-wikidata-real")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="t031-wikidata-real",
        artifact_path="test/t031.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


@pytest.mark.skipif(not REAL_TESTS, reason="LLMXIVE_REAL_TESTS not set")
class TestWikidataEntityFillReal:
    def test_wrong_capital_corrected_to_canberra(self, tmp_path):
        """fill_claim corrects 'capital of Australia is Sydney' to Canberra.

        Verified fact: Canberra (Q3960) is the capital of Australia (Q408).
        Sydney is the largest city but NOT the capital.
        """
        from llmxive.claims.models import ClaimKind
        from llmxive.fill.service import fill_claim

        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        claim = _make_claim(
            ClaimKind.ENTITY_FACT,
            "The capital of Australia is Sydney",
            resolved_value="Sydney",
        )
        result = fill_claim(
            claim,
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )

        assert result.status == "filled", (
            f"Expected filled for capital-of-Australia claim, got blocked: {result.reason!r}. "
            f"Channels tried: {result.channels_tried}"
        )
        assert result.value is not None
        # The corrected value must contain "Canberra" (case-insensitive)
        assert "canberra" in result.value.lower(), (
            f"Expected value containing 'Canberra', got {result.value!r}"
        )

        prov = result.provenance
        assert prov is not None
        assert prov.channel in ("wikidata", "wikipedia", "paper"), (
            f"Expected wikidata/wikipedia/paper provenance, got {prov.channel!r}"
        )
        assert prov.url.startswith("https://"), (
            f"provenance.url must be resolvable: {prov.url!r}"
        )
        # SC-002: value in fetched source text (via quote)
        assert "canberra" in prov.quote.lower() or "canberra" in prov.url.lower(), (
            f"SC-002: 'Canberra' not traceable in quote={prov.quote!r} or url={prov.url!r}"
        )

    def test_relational_claim_stays_blocked(self, tmp_path):
        """RELATIONAL claims are deferred in v1 — fill_claim must return blocked."""
        from llmxive.claims.models import ClaimKind
        from llmxive.fill.service import fill_claim

        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        claim = _make_claim(
            ClaimKind.RELATIONAL,
            "Australia has a higher GDP than New Zealand",
        )
        result = fill_claim(
            claim,
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )
        assert result.status == "blocked", (
            f"RELATIONAL claim should be blocked in v1, got {result.status!r} "
            f"value={result.value!r}"
        )
        assert result.channels_tried == [], (
            f"RELATIONAL should be blocked before channels are tried, got {result.channels_tried}"
        )

    def test_magnitude_claim_stays_blocked(self, tmp_path):
        """MAGNITUDE claims are deferred in v1 — fill_claim must return blocked."""
        from llmxive.claims.models import ClaimKind
        from llmxive.fill.service import fill_claim

        backend = _dartmouth_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key configured")

        claim = _make_claim(
            ClaimKind.MAGNITUDE,
            "Australia is the largest country in Oceania",
        )
        result = fill_claim(
            claim,
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )
        assert result.status == "blocked", (
            f"MAGNITUDE claim should be blocked in v1, got {result.status!r}"
        )
        assert result.channels_tried == []
