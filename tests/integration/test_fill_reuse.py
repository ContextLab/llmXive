"""T032 — integration test: fill-result cache round-trip (US4 reuse/invalidation).

Tests the REAL grounding cache put/get cycle without any network:
  - _store_cached then _load_cached returns the filled result (cache hit).
  - Changing the canonical text of the claim → cache miss (None).

No mocks, no stubs, no network calls.
"""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.models import FillProvenance, FillResult
from llmxive.fill.service import _load_cached, _store_cached


def _make_claim(canonical: str = "there are 9988 prime knots at 13 crossings") -> Claim:
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, canonical, "test-reuse-ctx")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=canonical,
        canonical=canonical,
        context="test-reuse-ctx",
        artifact_path="projects/PROJ-552/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


_PROVENANCE = FillProvenance(
    value="9988",
    source_id="A002863",
    url="https://oeis.org/A002863",
    quote="13 9988",
    channel="oeis",
    conflicts=[],
)

_FILL_RESULT = FillResult.filled("9988", _PROVENANCE, ["oeis"])


class TestFillCacheRoundTrip:
    """Real cache store/load with no network."""

    def test_store_then_load_returns_filled_result(self, tmp_path):
        """A stored FillResult.filled is retrieved as a filled result (cache hit)."""
        claim = _make_claim()
        _store_cached(claim, _FILL_RESULT, repo_root=tmp_path)
        loaded = _load_cached(claim, repo_root=tmp_path)

        assert loaded is not None, "Expected cache hit; got None"
        assert loaded.status == "filled"
        assert loaded.value == "9988"
        assert loaded.provenance is not None
        assert loaded.provenance.source_id == "A002863"
        assert loaded.provenance.url == "https://oeis.org/A002863"
        assert loaded.provenance.channel == "oeis"

    def test_cache_hit_no_new_search_needed(self, tmp_path):
        """A second call to _load_cached returns the same filled result."""
        claim = _make_claim()
        _store_cached(claim, _FILL_RESULT, repo_root=tmp_path)

        # Load twice — both should return the same cached result.
        first = _load_cached(claim, repo_root=tmp_path)
        second = _load_cached(claim, repo_root=tmp_path)

        assert first is not None
        assert second is not None
        assert first.value == second.value == "9988"

    def test_changed_canonical_is_cache_miss(self, tmp_path):
        """After changing the claim's canonical text, _load_cached returns None."""
        original_claim = _make_claim("there are 9988 prime knots at 13 crossings")
        _store_cached(original_claim, _FILL_RESULT, repo_root=tmp_path)

        # Different canonical → different cache key → miss.
        different_claim = _make_claim("there are 9988 prime knots at 14 crossings")
        result = _load_cached(different_claim, repo_root=tmp_path)

        assert result is None, "Expected cache miss for a different canonical; got hit"

    def test_no_repo_root_returns_none(self):
        """With repo_root=None, _load_cached returns None gracefully."""
        claim = _make_claim()
        result = _load_cached(claim, repo_root=None)
        assert result is None

    def test_store_blocked_and_reload(self, tmp_path):
        """A blocked FillResult is also persisted and retrieved correctly."""
        claim = _make_claim()
        blocked = FillResult.blocked("no source found", ["oeis", "wikipedia"])
        _store_cached(claim, blocked, repo_root=tmp_path)

        loaded = _load_cached(claim, repo_root=tmp_path)
        assert loaded is not None
        assert loaded.status == "blocked"
        assert loaded.reason == "no source found"
