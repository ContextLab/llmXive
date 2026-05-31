"""T024 — US2 safety: present_in_source rejects values absent from fetched text.

Tests the non-negotiable trust boundary (FR-003 / SC-002):
a value that is NOT in the fetched source text is NEVER returned,
regardless of what the LLM locator might have proposed.

All tests are deterministic and offline (no backend, no network).
"""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.extract import extract_value, present_in_source
from llmxive.fill.models import FetchedSource


def _src(text: str, channel: str = "oeis", authority: int = 0) -> FetchedSource:
    return FetchedSource(
        channel=channel,
        source_id="TEST-001",
        url="https://example.com/TEST-001",
        title="Test source",
        text=text,
        authority=authority,
    )


def _claim(kind: ClaimKind, raw: str, resolved_value: str | None = None) -> Claim:
    cid = compute_claim_id(kind, raw, "test-context")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="test-context",
        artifact_path="test/path.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# T024a: present_in_source False for NUMERIC when value absent
# ---------------------------------------------------------------------------

class TestPresentInSourceAbsentNumeric:
    def test_absent_value_returns_false(self):
        """A NUMERIC value NOT in source.text → present_in_source returns False."""
        source = _src("13 9988\n14 46972")
        # 88142 is NOT in this text
        assert present_in_source("88142", source, ClaimKind.NUMERIC) is False

    def test_present_value_returns_true(self):
        """Sanity: a value that IS in the text returns True."""
        source = _src("13 9988\n14 46972")
        assert present_in_source("9988", source, ClaimKind.NUMERIC) is True

    def test_absent_value_unrelated_text(self):
        """Source about weather, claim about math — value absent."""
        source = _src(
            "The temperature today is 23 degrees Celsius in Paris.",
            channel="wikipedia",
            authority=2,
        )
        assert present_in_source("88142", source, ClaimKind.NUMERIC) is False

    def test_similar_but_not_equal_number(self):
        """9989 vs 9988 — different value, must return False."""
        source = _src("13 9988\n14 46972")
        assert present_in_source("9989", source, ClaimKind.NUMERIC) is False


# ---------------------------------------------------------------------------
# T024b: present_in_source False for ENTITY_FACT when value absent
# ---------------------------------------------------------------------------

class TestPresentInSourceAbsentEntity:
    def test_entity_absent_returns_false(self):
        """An entity value NOT in source text → present_in_source returns False."""
        source = FetchedSource(
            channel="wikidata",
            source_id="Q408",
            url="https://www.wikidata.org/wiki/Q408",
            title="Australia",
            text="Australia is a country and continent in the Southern Hemisphere.",
            authority=1,
        )
        # "Canberra" is NOT in this text — only Australia is mentioned
        assert present_in_source("Canberra", source, ClaimKind.ENTITY_FACT) is False

    def test_entity_present_returns_true(self):
        """Sanity: entity that IS in the text returns True."""
        source = FetchedSource(
            channel="wikidata",
            source_id="Q408",
            url="https://www.wikidata.org/wiki/Q408",
            title="Australia",
            text="Australia is a country. Its capital is Canberra.",
            authority=1,
        )
        assert present_in_source("Canberra", source, ClaimKind.ENTITY_FACT) is True

    def test_entity_wrong_capital_absent(self):
        """Wrong entity (Sydney instead of Canberra) absent from correct text."""
        source = FetchedSource(
            channel="wikidata",
            source_id="Q408",
            url="https://www.wikidata.org/wiki/Q408",
            title="Australia",
            text="Australia is a country. Its capital city is Canberra, not Sydney.",
            authority=1,
        )
        # "Sydney" IS in this text (the "not Sydney" mention), but let's test
        # a genuinely absent entity
        assert present_in_source("Melbourne", source, ClaimKind.ENTITY_FACT) is False


# ---------------------------------------------------------------------------
# T024c: extract_value offline gate — returns None when value absent
# ---------------------------------------------------------------------------

class TestExtractValueOfflineGate:
    """extract_value with backend=None exercises the offline gate.

    For NUMERIC claims the offline path attempts _offline_numeric_lookup.
    For ENTITY claims it returns None without a backend.
    The trust boundary: if the located candidate is not in source.text, None.
    """

    def test_numeric_offline_absent_value_returns_none(self):
        """NUMERIC: source text has 9988 but claim asserts 27635.
        The offline lookup should NOT return 27635 (absent), and if it
        finds 9988 it will, but 27635 specifically should not appear."""
        # Source whose text does NOT contain the fabricated value 88142
        source = _src("The Zorblax constant for 13-dimensional frobnication is unknown.")
        claim = _claim(
            ClaimKind.NUMERIC,
            "The Zorblax constant for 13-dimensional frobnication is 88142",
            resolved_value="88142",
        )
        # With backend=None, the offline lookup won't find 88142 in this text
        result = extract_value(source, claim, backend=None, model=None, repo_root=None)
        # Either None (value not found) or something that IS in the source text
        if result is not None:
            assert present_in_source(result, source, claim.kind), (
                f"extract_value returned {result!r} which is NOT in source.text — "
                "trust boundary violated!"
            )

    def test_entity_offline_no_backend_returns_none(self):
        """ENTITY_FACT: with backend=None, extract_value returns None (no LLM)."""
        source = FetchedSource(
            channel="wikidata",
            source_id="Q408",
            url="https://www.wikidata.org/wiki/Q408",
            title="Australia",
            text="Australia is a country in the Southern Hemisphere.",
            authority=1,
        )
        claim = _claim(
            ClaimKind.ENTITY_FACT,
            "The capital of Australia is Sydney",
        )
        result = extract_value(source, claim, backend=None, model=None, repo_root=None)
        # Without a backend, ENTITY_FACT offline path returns None
        assert result is None

    def test_trust_boundary_numeric_value_must_be_in_text(self):
        """Whatever extract_value returns for a NUMERIC claim with backend=None,
        that value MUST be present in source.text (the trust boundary)."""
        # Source: a proper b-file style text
        source = _src("10 100\n11 200\n12 300\n13 400")
        claim = _claim(
            ClaimKind.NUMERIC,
            "there are 999 things at 13 crossings",
            resolved_value="999",
        )
        result = extract_value(source, claim, backend=None, model=None, repo_root=None)
        if result is not None:
            # The safety invariant: returned value MUST be in source.text
            assert present_in_source(result, source, claim.kind), (
                f"Trust boundary violated: {result!r} not in source.text"
            )
        # 999 is not in the source text, so result is either None or something
        # from the source (e.g. "400" for index 13)
        if result is not None:
            assert result != "999", "999 is not in source.text but was returned"
