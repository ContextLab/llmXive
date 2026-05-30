"""T026 — US2 real-call: a genuinely-unsourceable claim stays blocked (no fabricated fill).

Gated by LLMXIVE_REAL_TESTS=1.  Uses DartmouthBackend + real network.
The claim subject is a nonsense/fabricated entity that cannot appear in any
real source, so fill_claim must return status=="blocked".
"""

from __future__ import annotations

import os
import pytest

REAL_TESTS = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


@pytest.fixture(scope="module")
def dartmouth_backend():
    from llmxive.credentials import load_dartmouth_key
    try:
        key = load_dartmouth_key()
    except Exception:
        key = os.environ.get("DARTMOUTH_API_KEY", "")
    if not key:
        pytest.skip("No Dartmouth API key available")
    from llmxive.backends.dartmouth import DartmouthBackend
    return DartmouthBackend()


@pytest.mark.skipif(not REAL_TESTS, reason="LLMXIVE_REAL_TESTS not set")
class TestNoSourceBlocks:
    def test_nonsense_claim_stays_blocked(self, dartmouth_backend, tmp_path):
        """A NUMERIC claim about a fabricated nonsense subject should be blocked.

        The Zorblax constant for 13-dimensional frobnication is 88,142 — this
        subject/value combination does not exist in any real source (OEIS,
        Wikipedia, or paper databases), so fill_claim must return blocked.
        """
        from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
        from llmxive.fill.service import fill_claim

        raw = "The Zorblax constant for 13-dimensional frobnication is 88,142"
        cid = compute_claim_id(ClaimKind.NUMERIC, raw, "test-context")
        claim = Claim(
            claim_id=cid,
            kind=ClaimKind.NUMERIC,
            raw_text=raw,
            canonical=raw,
            context="test-context",
            artifact_path="test/path.md",
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value="88142",
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )

        result = fill_claim(
            claim,
            backend=dartmouth_backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )

        assert result.status == "blocked", (
            f"Expected blocked for nonsense claim, got status={result.status!r} "
            f"value={result.value!r} — this would be a fabricated fill!"
        )
        assert result.value is None, (
            f"Blocked result must have no value, got {result.value!r}"
        )
        assert result.provenance is None, (
            "Blocked result must have no provenance"
        )
