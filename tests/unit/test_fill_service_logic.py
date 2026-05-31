"""T018 — unit tests for fill_claim pure guard branches (offline, no mock backend).

Tests only the deterministic guard paths that do NOT touch network/LLM:
  - claim.kind not in {NUMERIC, ENTITY_FACT} → FillResult.blocked
  - kind is fillable but channels return no sources → blocked
    (exercised by passing a NUMERIC claim with no A-numbers and no network)

These tests must pass fully offline.  The full search path is real-call
tested in T021-T023.
"""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.models import FillResult
from llmxive.fill.service import fill_claim


def _make_claim(kind: ClaimKind, raw: str, canonical: str | None = None,
                resolved_value: str | None = None) -> Claim:
    cid = compute_claim_id(kind, canonical or raw, "test-context")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=canonical or raw,
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


class TestKindGuard:
    """CAUSAL/CITATION/RESULT are still blocked; MAGNITUDE/RELATIONAL now fillable
    (spec 018, T020/T023) — they reach channels, but with no network they block
    on 'value not present in any fetched source'."""

    def test_magnitude_blocked_no_sources(self, monkeypatch):
        """MAGNITUDE is now fillable (spec 018); with all channels returning []
        offline it is blocked at 'not present in any fetched source', not at the
        kind guard."""
        from llmxive.fill.channels import papers, wikipedia
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(ClaimKind.MAGNITUDE, "X is the largest Y")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert isinstance(result, FillResult)
        assert result.status == "blocked"
        # channels were tried (kind guard no longer fires); reason is no source
        assert "not fillable" not in result.reason

    def test_relational_blocked_no_sources(self, monkeypatch):
        """RELATIONAL is now fillable (spec 018); blocked only when channels empty."""
        from llmxive.fill.channels import papers, wikipedia
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(ClaimKind.RELATIONAL, "A is related to B")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert "not fillable" not in result.reason

    def test_causal_blocked(self):
        claim = _make_claim(ClaimKind.CAUSAL, "X causes Y")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert result.channels_tried == []

    def test_citation_blocked(self):
        # CITATION is handled by resolve_numeric_or_citation, not fill v1
        claim = _make_claim(ClaimKind.CITATION, "Smith et al. 2020 found 42")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert result.channels_tried == []

    def test_result_blocked(self):
        claim = _make_claim(ClaimKind.RESULT, "result: 42")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert result.channels_tried == []


class TestNoSourcesBlocked:
    """A fillable claim that has no A-numbers (OEIS won't fire) and no network
    (offline) should reach the 'value not present in any fetched source' branch."""

    def test_numeric_no_a_numbers_no_network(self, monkeypatch):
        """NUMERIC claim with no A-numbers: OEIS channel returns [], other channels
        are patched to return [] to avoid real HTTP calls in unit tests."""
        from llmxive.fill.channels import oeis, papers, wikipedia

        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])
        # oeis.search_and_fetch already returns [] for no A-numbers; but patch too
        monkeypatch.setattr(oeis, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(oeis, "fetch_bfile", lambda a, **kw: {})

        claim = _make_claim(
            ClaimKind.NUMERIC,
            "there are 100 widgets in the set",
            resolved_value="100",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert "not present" in result.reason

    def test_entity_fact_no_sources(self, monkeypatch):
        """ENTITY_FACT with all channels patched to [] → blocked."""
        from llmxive.fill.channels import papers, wikipedia
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(
            ClaimKind.ENTITY_FACT,
            "The capital of France is Berlin",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"


class TestFillResultContract:
    """Validate FillResult factory invariants used by the service."""

    def test_blocked_has_no_value(self):
        result = FillResult.blocked("test reason", [])
        assert result.status == "blocked"
        assert result.value is None
        assert result.provenance is None

    def test_channels_tried_preserved_magnitude(self, monkeypatch):
        """MAGNITUDE is now fillable (spec 018, T020); channels_tried contains the
        channels that were attempted (not [] as when kind-blocked).  With all
        channels patched to [] the result is still blocked but channels_tried is
        non-empty, proving the kind guard no longer fires."""
        from llmxive.fill.channels import papers, wikipedia
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(ClaimKind.MAGNITUDE, "X is largest")
        result = fill_claim(claim)
        # Kind is now fillable → channels were tried (list non-empty)
        assert result.status == "blocked"
        assert isinstance(result.channels_tried, list)
