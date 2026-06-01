"""Tests for arXiv-call-volume reductions in the authoritative-fill layer.

These tests pin the LOGIC of four fixes (no external services mocked — only
deterministic in-process doubles standing in for the network fetchers, while the
real code under test runs):

A — Stable, rephrase-independent fill cache key (fact fingerprint).
B — Negative-result cache for failed per-candidate lookups.
D — Circuit-breaker short-circuit in ArxivClient.get_by_id + shared client.
E — Cap/gate the theorem channel.

All tests must pass fully offline.
"""

from __future__ import annotations

import time
import types

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id


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


# ---------------------------------------------------------------------------
# Fix A — fact fingerprint cache key
# ---------------------------------------------------------------------------

class TestFactFingerprintCacheKey:
    """The fill verdict cache must key on a FACT FINGERPRINT (number + subject
    keywords), NOT the raw canonical, so the convergence reviser's per-round
    rephrasings of the same fact share one cache entry — while two genuinely
    different facts never collide."""

    def _key(self, claim: Claim):
        from llmxive.fill.service import _cache_key_parts
        return _cache_key_parts(claim)

    def test_rephrasings_of_same_fact_share_key(self):
        """Two rephrasings of '27,635 prime knots at 13 crossings' → SAME key."""
        c1 = _make_claim(
            ClaimKind.NUMERIC,
            "There are 27,635 prime knots with 13 crossings.",
        )
        c2 = _make_claim(
            ClaimKind.NUMERIC,
            "The number of prime knots at crossing number 13 is 27635.",
        )
        assert self._key(c1) == self._key(c2)

    def test_different_numbers_same_subject_do_not_collide(self):
        """'9988 prime knots…' vs '27635 prime knots…' → DIFFERENT keys.

        Critical correctness: same subject but a different asserted number must
        not share a cache entry (would serve a wrong filled value)."""
        c1 = _make_claim(
            ClaimKind.NUMERIC,
            "There are 9988 prime knots with 12 crossings.",
        )
        c2 = _make_claim(
            ClaimKind.NUMERIC,
            "There are 27635 prime knots with 13 crossings.",
        )
        # NOTE: the crossing index (12 vs 13) AND the count (9988 vs 27635)
        # both differ — these are different facts and MUST get different keys.
        assert self._key(c1) != self._key(c2)

    def test_two_unrelated_facts_do_not_collide(self):
        """Completely unrelated facts → different keys."""
        c1 = _make_claim(
            ClaimKind.NUMERIC,
            "The boiling point of water is 100 degrees Celsius.",
        )
        c2 = _make_claim(
            ClaimKind.NUMERIC,
            "There are 27635 prime knots with 13 crossings.",
        )
        assert self._key(c1) != self._key(c2)

    def test_key_is_deterministic(self):
        c = _make_claim(ClaimKind.NUMERIC, "There are 27,635 prime knots.")
        assert self._key(c) == self._key(c)


# ---------------------------------------------------------------------------
# Fix D — circuit-breaker short-circuit in get_by_id
# ---------------------------------------------------------------------------

class TestArxivGetByIdBreaker:
    """ArxivClient.get_by_id must respect the same circuit breaker that
    search() does, so the per-candidate path stops hitting arXiv once tripped."""

    def test_get_by_id_short_circuits_when_breaker_tripped(self, monkeypatch):
        from llmxive.librarian.search import ArxivClient

        client = ArxivClient(min_interval_seconds=0)
        client._disabled_until = time.monotonic() + 30.0

        # If get_by_id touched the network it would call _wait_for_slot; assert
        # it does NOT (short-circuit returns None without any network attempt).
        called = {"wait": False}
        orig_wait = client._wait_for_slot

        def _tracking_wait():
            called["wait"] = True
            orig_wait()

        monkeypatch.setattr(client, "_wait_for_slot", _tracking_wait)
        out = client.get_by_id("1706.03762")
        assert out is None
        assert called["wait"] is False

    def test_get_by_id_proceeds_when_breaker_clear(self, monkeypatch):
        """With the breaker clear, get_by_id reaches the network path (here a
        deterministic in-process arxiv stand-in)."""
        from llmxive.librarian import search as search_mod

        mod = types.ModuleType("arxiv")

        class _Result:
            entry_id = "http://arxiv.org/abs/1706.03762v1"
            title = "Attention Is All You Need"
            authors: list = []  # noqa: RUF012 - inert test stand-in
            published = None
            summary = "abstract"

        class _Client:
            def __init__(self, *a, **k):
                pass

            def results(self, search):
                return iter([_Result()])

        class _Search:
            def __init__(self, *a, **k):
                pass

        mod.Client = _Client
        mod.Search = _Search

        import sys
        monkeypatch.setitem(sys.modules, "arxiv", mod)
        client = search_mod.ArxivClient(min_interval_seconds=0)
        cand = client.get_by_id("1706.03762")
        assert cand is not None
        assert cand.primary_pointer == "1706.03762"


class TestTheoremSearchSharesArxivClient:
    """The fill theorem channel must thread a SHARED ArxivClient through
    TheoremSearchClient so a tripped breaker is honoured across candidates."""

    def test_theorem_channel_uses_shared_arxiv_client(self):
        from llmxive.fill.channels import theorem

        c1 = theorem._shared_arxiv_client()
        c2 = theorem._shared_arxiv_client()
        assert c1 is c2  # module-level singleton

    def test_theoremsearch_client_built_with_shared_arxiv(self, monkeypatch):
        """When theorem.search_and_fetch builds its TheoremSearchClient it must
        pass the shared ArxivClient as arxiv_client=."""
        from llmxive.fill.channels import theorem
        from llmxive.librarian import theoremsearch as ts_mod

        captured = {}

        class _FakeTS:
            def __init__(self, *a, arxiv_client=None, **k):
                captured["arxiv_client"] = arxiv_client

            def search(self, query, *, limit=10):
                return []

        monkeypatch.setattr(ts_mod, "TheoremSearchClient", _FakeTS)
        # theorem.py imports the symbol directly; patch there too.
        monkeypatch.setattr(theorem, "TheoremSearchClient", _FakeTS)

        claim = _make_claim(ClaimKind.NUMERIC, "some math claim about knots")
        theorem.search_and_fetch("knots", claim)
        assert captured["arxiv_client"] is theorem._shared_arxiv_client()


# ---------------------------------------------------------------------------
# Fix B — negative-result cache for failed per-candidate lookups
# ---------------------------------------------------------------------------

class TestTheoremNegativeCache:
    """A failed (channel, arxiv_id) retrieve must be remembered so a second
    resolution of the same id does NOT call the fetcher again."""

    def test_failed_candidate_not_refetched(self, monkeypatch, tmp_path):
        from llmxive.fill.channels import theorem
        from llmxive.librarian.search import Candidate

        # One candidate that always fails to retrieve (returns None doc).
        cand = Candidate(
            backend="theoremsearch",
            primary_pointer="2301.99999",
            claimed_title="Phantom paper",
            claimed_authors=[],
            claimed_year=2023,
            claimed_venue="arXiv",
            claimed_abstract=None,
        )

        class _FakeTS:
            def __init__(self, *a, **k):
                pass

            def search(self, query, *, limit=10):
                return [cand]

        monkeypatch.setattr(theorem, "TheoremSearchClient", _FakeTS)

        calls = {"n": 0}

        def _fake_retrieve(candidate, *, timeout):
            calls["n"] += 1
            return None  # simulate 503 / empty PDF

        monkeypatch.setattr(theorem, "_retrieve_for_candidate", _fake_retrieve)
        # Reset any in-process memo so the test is order-independent.
        theorem._reset_negative_cache()

        claim = _make_claim(ClaimKind.NUMERIC, "math claim about knots")

        out1 = theorem.search_and_fetch("knots", claim, repo_root=tmp_path)
        out2 = theorem.search_and_fetch("knots", claim, repo_root=tmp_path)
        assert out1 == []
        assert out2 == []
        # Second resolution must NOT re-call the fetcher for the same failed id.
        assert calls["n"] == 1

    def test_negative_cache_scoped_to_id_not_whole_claim(self, monkeypatch, tmp_path):
        """A negative entry for id A must not block a resolvable id B."""
        from llmxive.fill.channels import theorem
        from llmxive.grounding.full_text import RetrievedDoc
        from llmxive.librarian.search import Candidate

        bad = Candidate(
            backend="theoremsearch", primary_pointer="2301.00001",
            claimed_title="bad", claimed_authors=[], claimed_year=2023,
            claimed_venue="arXiv", claimed_abstract=None,
        )
        good = Candidate(
            backend="theoremsearch", primary_pointer="2301.00002",
            claimed_title="good", claimed_authors=[], claimed_year=2023,
            claimed_venue="arXiv", claimed_abstract=None,
        )

        class _FakeTS:
            def __init__(self, *a, **k):
                pass

            def search(self, query, *, limit=10):
                return [bad, good]

        monkeypatch.setattr(theorem, "TheoremSearchClient", _FakeTS)

        def _fake_retrieve(candidate, *, timeout):
            if candidate.primary_pointer == "2301.00002":
                return RetrievedDoc("arxiv", "2301.00002", "arxiv",
                                    "the answer is 42", None,
                                    "good", "http://x/2301.00002")
            return None

        monkeypatch.setattr(theorem, "_retrieve_for_candidate", _fake_retrieve)
        theorem._reset_negative_cache()

        claim = _make_claim(ClaimKind.NUMERIC, "math claim about knots")
        out = theorem.search_and_fetch("knots", claim, repo_root=tmp_path)
        # The good candidate still resolves despite the bad one being negative-cached.
        assert len(out) == 1
        assert out[0].source_id == "2301.00002"


# ---------------------------------------------------------------------------
# Fix E — gate/cap the theorem channel
# ---------------------------------------------------------------------------

class TestTheoremChannelGating:
    """Once a higher-authority channel (constants/OEIS/wikipedia) produces a
    verified fill, the theorem channel must NOT run for that claim."""

    def test_max_candidates_capped_at_two(self):
        from llmxive.fill.channels import theorem
        assert theorem._MAX_CANDIDATES == 2

    def test_theorem_skipped_when_higher_authority_resolves(self, monkeypatch):
        """A NUMERIC math claim whose value is present in an OEIS source must
        NOT invoke the theorem channel (break on first verified fill)."""
        from llmxive.fill import service
        from llmxive.fill.channels import oeis, theorem, wikipedia
        from llmxive.fill.models import FetchedSource

        # Force math classification so theorem is in the channel list at all.
        monkeypatch.setattr(service, "_is_math_claim", lambda *a, **k: True)

        # OEIS resolves the value.
        oeis_src = FetchedSource(
            channel="oeis", source_id="A002863",
            url="https://oeis.org/A002863", title="A002863",
            text="13 27635\n", authority=1,
        )
        monkeypatch.setattr(oeis, "search_and_fetch", lambda q, c, **kw: [oeis_src])
        monkeypatch.setattr(wikipedia, "search_and_fetch", lambda q, c, **kw: [])

        # If theorem runs, this flag flips. It must NOT.
        ran = {"theorem": False}

        def _theorem_guard(q, c, **kw):
            ran["theorem"] = True
            return []

        monkeypatch.setattr(theorem, "search_and_fetch", _theorem_guard)

        claim = _make_claim(
            ClaimKind.NUMERIC,
            "There are 27635 prime knots with 13 crossings.",
        )
        result = service.fill_claim(claim, backend=None, model=None, repo_root=None)
        assert result.status == "filled"
        assert result.value == "27635"
        assert ran["theorem"] is False
        assert "theorem" not in result.channels_tried
