"""T015 (spec 018, US2) — the constants channel resolves with ZERO network.

A recognized constant's true value comes from the library-backed table
(`math`/`scipy.constants`), so the constants fill channel must make no HTTP
call. We wrap the real librarian HTTP helper with a counter and assert it stays
flat while the channel returns a populated FetchedSource with its authority.
"""

from __future__ import annotations

import llmxive.librarian.search as _search
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.channels import AUTHORITY, constants


def _pi_claim() -> Claim:
    return Claim(
        claim_id="c_pi",
        kind=ClaimKind.NUMERIC,
        raw_text="pi is approximately 3.14",
        canonical="pi",
        context="",
        artifact_path="projects/PROJ-1/spec.md",
        source_type="external",
        status=ClaimStatus.NOT_ENOUGH_INFO,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="",
    )


def test_constants_channel_makes_no_http(monkeypatch):
    calls: list[int] = []
    real = _search._retry_request

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(_search, "_retry_request", counting)

    sources = constants.search_and_fetch("pi", _pi_claim(), timeout=30.0)

    # The channel returned the library value with provenance, and made NO HTTP.
    assert calls == []
    assert len(sources) == 1
    src = sources[0]
    assert src.channel == "constants"
    assert src.authority == AUTHORITY["constants"]
    assert "3.14159" in src.text          # the true library value
    assert src.url                         # a resolvable authority url
    assert "math.pi" in src.text or "pi" in src.text.lower()


def test_constants_channel_unknown_subject_returns_empty(monkeypatch):
    calls: list[int] = []
    real = _search._retry_request
    monkeypatch.setattr(
        _search, "_retry_request",
        lambda *a, **k: (calls.append(1), real(*a, **k))[1],
    )
    claim = _pi_claim()
    claim.canonical = "the florbnax constant"
    claim.raw_text = "the florbnax constant is 7.2"
    assert constants.search_and_fetch("florbnax constant", claim) == []
    assert calls == []   # still no network for an unknown subject
