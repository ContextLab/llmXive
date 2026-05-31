"""T012 — Real-call: approximate mode, constants path (zero network).

Most assertions are offline (verify.constants uses math/scipy — no network).
Gated by LLMXIVE_REAL_TESTS=1 per convention, but the constants path itself
makes ZERO HTTP calls — that invariant is asserted here.
"""

from __future__ import annotations

import os

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to run real-call tests",
)


def _claim(text: str, kind: ClaimKind = ClaimKind.NUMERIC) -> Claim:
    cid = compute_claim_id(kind, text, "test-real")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=text,
        canonical=text,
        context="test-real",
        artifact_path="test-real",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-01-01T00:00:00Z",
    )


@pytest.fixture(autouse=True)
def enable_fill(monkeypatch):
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")


# ---------------------------------------------------------------------------
# Zero-network counter for the constants path
# ---------------------------------------------------------------------------

class HTTPCallCounter:
    """Wraps the real _retry_request to count HTTP calls."""

    def __init__(self):
        self.count = 0
        self._original = None

    def install(self):
        try:
            import llmxive.librarian.fetch as _fetch_mod
            self._original = _fetch_mod._retry_request
            counter = self

            def _counting(*args, **kwargs):
                counter.count += 1
                return counter._original(*args, **kwargs)

            _fetch_mod._retry_request = _counting
        except (ImportError, AttributeError):
            pass

    def uninstall(self):
        if self._original is not None:
            try:
                import llmxive.librarian.fetch as _fetch_mod
                _fetch_mod._retry_request = self._original
            except (ImportError, AttributeError):
                pass


@pytest.fixture
def http_counter():
    c = HTTPCallCounter()
    c.install()
    yield c
    c.uninstall()


# ---------------------------------------------------------------------------
# T012-A: "π is 3.14" → VERIFIED, value preserved as 3.14
# ---------------------------------------------------------------------------

def test_pi_3_14_verified(tmp_path, http_counter):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.14")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate"
    assert verdict.value == "3.14"
    # Constants path: zero network
    assert http_counter.count == 0, f"Expected 0 HTTP calls, got {http_counter.count}"


# ---------------------------------------------------------------------------
# T012-B: "π is about 3" → VERIFIED (hedge allows 0 decimals)
# ---------------------------------------------------------------------------

def test_pi_about_3_verified(tmp_path, http_counter):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is about 3")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate"
    assert http_counter.count == 0


# ---------------------------------------------------------------------------
# T012-C: "π is 3.14159" → VERIFIED (5 dp rounding)
# ---------------------------------------------------------------------------

def test_pi_5dp_verified(tmp_path, http_counter):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.14159")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate"
    assert http_counter.count == 0


# ---------------------------------------------------------------------------
# T012-D: "π is 3.15" → VERIFIED corrected to "3.14" (evidence.corrected)
# ---------------------------------------------------------------------------

def test_pi_3_15_corrected(tmp_path, http_counter):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.15")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate"
    assert evidence.get("corrected") is True
    assert verdict.value == "3.14"
    assert http_counter.count == 0


# ---------------------------------------------------------------------------
# T012-E: "e is 2.5" → VERIFIED corrected (2.5 is not a valid rounding of e)
# ---------------------------------------------------------------------------

def test_e_2_5_corrected(tmp_path, http_counter):
    from llmxive.claims.resolve import resolve

    claim = _claim("e is 2.5")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate"
    assert evidence.get("corrected") is True
    # Corrected value should be 2.7 (1 decimal place, round(e, 1) = 2.7)
    assert verdict.value == "2.7", f"Expected '2.7', got {verdict.value!r}"
    assert http_counter.count == 0


# ---------------------------------------------------------------------------
# T012-F: Provenance names the authority + URL
# ---------------------------------------------------------------------------

def test_pi_provenance(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.14")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    evidence = verdict.evidence or {}
    # Must have authority info somewhere in evidence
    assert "authority" in evidence or "constant" in evidence, \
        f"Expected provenance in evidence: {evidence}"
