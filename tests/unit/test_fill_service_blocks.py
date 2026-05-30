"""T025 — US2: fill_claim returns blocked when no fetched source yields a gate-passing value.

Tests the deterministic blocked path:
- A NUMERIC claim whose channels (oeis/wikipedia/paper) all return no usable sources
  → fill_claim returns FillResult with status=="blocked" and
    reason containing "not present in any fetched source".
- Channels are controlled by monkeypatching their search_and_fetch to return []
  so no real HTTP is attempted (offline, deterministic).
- backend=None ensures the offline path.
- Also tests: provenance is ONLY built from sources whose text contains the value
  (the positive path is tested by verifying the blocked path's contract).
"""

from __future__ import annotations

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.models import FillResult
from llmxive.fill.service import fill_claim


def _make_claim(kind: ClaimKind, raw: str, resolved_value: str | None = None) -> Claim:
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


class TestFillClaimBlockedPath:
    """fill_claim must return blocked when no source passes the present-in-source gate."""

    def test_numeric_all_channels_empty_blocked(self, monkeypatch):
        """NUMERIC: all channels return [] → blocked with correct reason."""
        from llmxive.fill.channels import oeis, wikipedia, papers

        monkeypatch.setattr(oeis, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(oeis, "fetch_bfile", lambda a, **kw: {})
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(
            ClaimKind.NUMERIC,
            "there are 88142 widgets in the zorblax set",
            resolved_value="88142",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)

        assert isinstance(result, FillResult)
        assert result.status == "blocked"
        assert "not present" in result.reason
        assert result.value is None
        assert result.provenance is None

    def test_numeric_blocked_channels_tried_recorded(self, monkeypatch):
        """When channels are tried but return no sources, channels_tried is populated."""
        from llmxive.fill.channels import oeis, wikipedia, papers

        monkeypatch.setattr(oeis, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(oeis, "fetch_bfile", lambda a, **kw: {})
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(
            ClaimKind.NUMERIC,
            "there are 88142 widgets in the zorblax set",
            resolved_value="88142",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        # channels_tried should include the ones that were attempted
        assert isinstance(result.channels_tried, list)

    def test_entity_all_channels_empty_blocked(self, monkeypatch):
        """ENTITY_FACT: all channels return [] → blocked."""
        from llmxive.fill.channels import wikipedia, papers

        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass

        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(
            ClaimKind.ENTITY_FACT,
            "The capital of Zorblaxia is Frobnopolis",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)

        assert result.status == "blocked"
        assert result.value is None
        assert result.provenance is None

    def test_magnitude_blocked_no_sources(self, monkeypatch):
        """MAGNITUDE is now fillable (spec 018, T020); with all channels returning []
        offline it is blocked at 'not present in any fetched source', not the kind
        guard ('not fillable' must NOT appear in the reason)."""
        from llmxive.fill.channels import wikipedia, papers
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(ClaimKind.MAGNITUDE, "X is the tallest Y")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert "not fillable" not in result.reason

    def test_relational_blocked_no_sources(self, monkeypatch):
        """RELATIONAL is now fillable (spec 018, T023); blocked only when channels empty."""
        from llmxive.fill.channels import wikipedia, papers
        try:
            from llmxive.fill.channels import wikidata
            monkeypatch.setattr(wikidata, "search_and_fetch", lambda q, c, **kw: [])
        except (ImportError, AttributeError):
            pass
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(ClaimKind.RELATIONAL, "A is related to B via C")
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert "not fillable" not in result.reason

    def test_blocked_result_has_no_provenance(self, monkeypatch):
        """A blocked result MUST NOT carry provenance (trust boundary: provenance
        only built from a source whose text contains the value)."""
        from llmxive.fill.channels import oeis, wikipedia, papers

        monkeypatch.setattr(oeis, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(oeis, "fetch_bfile", lambda a, **kw: {})
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])
        monkeypatch.setattr(papers, "search_and_fetch", lambda q, c, **kw: [])

        claim = _make_claim(
            ClaimKind.NUMERIC,
            "there are 99999 things",
            resolved_value="99999",
        )
        result = fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "blocked"
        assert result.provenance is None, (
            "Blocked result must not carry provenance — "
            "provenance is only built from a source whose text contains the value"
        )
