"""T037 — contract test: each fill channel exposes the required interface.

Asserts:
1. Each channel module exposes `search_and_fetch(query, claim, *, timeout=...)`.
2. Offline: fixture-based FetchedSource contract (non-empty text, plausible URL).
3. Live (gated by LLMXIVE_REAL_TESTS): real channel call returns valid FetchedSource list.
"""

from __future__ import annotations

import importlib
import inspect
import os

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.models import FetchedSource

# ---------------------------------------------------------------------------
# Channel module names
# ---------------------------------------------------------------------------

CHANNEL_MODULES = [
    "llmxive.fill.channels.oeis",
    "llmxive.fill.channels.wikipedia",
    "llmxive.fill.channels.wikidata",
    "llmxive.fill.channels.papers",
    "llmxive.fill.channels.theorem",
]


def _make_claim() -> Claim:
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, "9988 prime knots at 13 crossings", "contract-ctx")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text="9988 prime knots at 13 crossings",
        canonical="9988 prime knots at 13 crossings",
        context="contract-ctx",
        artifact_path="projects/PROJ-552/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Offline: signature contract
# ---------------------------------------------------------------------------

class TestChannelSignatureContract:
    """Each channel module must expose search_and_fetch with the required signature."""

    @pytest.mark.parametrize("module_path", CHANNEL_MODULES)
    def test_exposes_search_and_fetch(self, module_path):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "search_and_fetch"), (
            f"{module_path} does not expose search_and_fetch"
        )
        fn = mod.search_and_fetch
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        # Positional: query, claim
        assert "query" in params, f"{module_path}.search_and_fetch missing 'query' parameter"
        assert "claim" in params, f"{module_path}.search_and_fetch missing 'claim' parameter"
        # Keyword: timeout (with default)
        assert "timeout" in params, f"{module_path}.search_and_fetch missing 'timeout' parameter"
        timeout_param = sig.parameters["timeout"]
        assert timeout_param.default is not inspect.Parameter.empty, (
            f"{module_path}.search_and_fetch 'timeout' must have a default value"
        )


# ---------------------------------------------------------------------------
# Offline: FetchedSource fixture contract (pure adapters only)
# ---------------------------------------------------------------------------

class TestFetchedSourceContract:
    """FetchedSource objects must satisfy the data-model contract."""

    def test_fetched_source_non_empty_text(self):
        """A FetchedSource must have non-empty text (constructor enforces this)."""
        with pytest.raises(ValueError, match="non-empty"):
            FetchedSource(
                channel="oeis",
                source_id="A002863",
                url="https://oeis.org/A002863",
                title="A002863",
                text="",           # empty → must raise
                authority=0,
            )

    def test_fetched_source_valid_fields(self):
        """A well-formed FetchedSource passes validation."""
        src = FetchedSource(
            channel="oeis",
            source_id="A002863",
            url="https://oeis.org/A002863",
            title="Number of prime knots with n crossings",
            text="13 9988\n14 46972\n",
            authority=0,
        )
        assert src.text, "text must be non-empty"
        assert src.url.startswith("http"), "url must be resolvable-looking"
        assert src.source_id, "source_id must be non-empty"
        assert src.channel in {"oeis", "wikidata", "wikipedia", "theorem", "paper"}, (
            f"unexpected channel {src.channel!r}"
        )

    def test_fetched_source_url_looks_resolvable(self):
        """A FetchedSource url must start with http or https."""
        src = FetchedSource(
            channel="wikipedia",
            source_id="Prime_knot",
            url="https://en.wikipedia.org/wiki/Prime_knot",
            title="Prime knot",
            text="A prime knot is a non-trivial knot that cannot be decomposed.",
            authority=2,
        )
        assert src.url.startswith("https://"), "url must start with https://"


# ---------------------------------------------------------------------------
# Live: real channel calls (gated by LLMXIVE_REAL_TESTS)
# ---------------------------------------------------------------------------

REAL = pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="set LLMXIVE_REAL_TESTS=1 to run live channel tests",
)


class TestChannelLiveContract:

    @REAL
    def test_oeis_search_and_fetch_returns_fetched_sources(self):
        from llmxive.fill.channels import oeis

        # Force an A-number into the claim text so oeis.search_and_fetch finds it.
        kind = ClaimKind.NUMERIC
        cid = compute_claim_id(kind, "A002863 prime knots at 13 crossings", "contract-live")
        live_claim = Claim(
            claim_id=cid,
            kind=kind,
            raw_text="A002863 prime knots at 13 crossings",
            canonical="A002863 prime knots at 13 crossings",
            context="contract-live",
            artifact_path="projects/PROJ-552/idea/foo.md",
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )
        results = oeis.search_and_fetch("A002863 prime knots", live_claim, timeout=30.0)
        # Must return a list (may be empty on network failure, but if non-empty must be valid).
        assert isinstance(results, list)
        for src in results:
            assert isinstance(src, FetchedSource)
            assert src.text, "text must be non-empty"
            assert src.url.startswith("http"), "url must be resolvable-looking"

    @REAL
    def test_wikipedia_search_and_fetch_returns_fetched_sources(self):
        from llmxive.fill.channels import wikipedia

        claim = _make_claim()
        results = wikipedia.search_and_fetch(
            "number of prime knots by crossing number", claim, timeout=30.0
        )
        assert isinstance(results, list)
        for src in results:
            assert isinstance(src, FetchedSource)
            assert src.text
            assert src.url.startswith("http")
