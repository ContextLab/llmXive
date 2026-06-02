"""Real-call acceptance matrix for spec 019 (semantic substantiation gate).

Run with ``LLMXIVE_REAL_TESTS=1`` and a Dartmouth key (resolved inside
``DartmouthBackend`` via ``llmxive.credentials`` — the models used are free).
``model=None`` lets the central router default to qwen with peer fallback
(gpt-oss / gemma) so a qwen flap does not flake the matrix.

Covers (each a Success Criterion):
  * SC-001  the "≤6 / Almoravid dynasty" coincidental match → BLOCKED, never 6
  * SC-004  "capital of France is Paris" with a supporting body → grounded → kept
  * SC-005  "capital of Australia is Sydney" vs a Canberra body → never grounded
  * SC-006  a bound claim is blocked BEFORE any fetch (real backend available)
  * SC-002/SC-003 (by construction) STRUCTURED channels skip the prose gate; the
            full 9988/π end-to-end no-regression is covered by the OFFLINE suites
            tests/integration/test_exact_count_no_regress.py and
            tests/unit/test_fill_constants_channel.py (run in the offline gate).
"""

from __future__ import annotations

import os

import pytest

from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.channels import is_structured
from llmxive.fill.extract import _accept
from llmxive.fill.models import FetchedSource
from llmxive.fill.relevance import prose_substantiated
from llmxive.fill.service import fill_claim

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call"
)


def _claim(kind: ClaimKind, raw: str) -> Claim:
    return Claim(
        claim_id="c", kind=kind, raw_text=raw, canonical=raw, context="",
        artifact_path="specs/x/spec.md", source_type="external",
        status=ClaimStatus.PENDING, resolved_value=None, evidence=None,
        resolver=None, attempts=0, updated_at="2026-06-02T00:00:00Z",
    )


def _prose(text: str, *, channel: str = "wikipedia", title: str = "x") -> FetchedSource:
    return FetchedSource(
        channel=channel, source_id="s", url="https://en.wikipedia.org/wiki/x",
        title=title, text=text, authority=3,
    )


# --- SC-001 : the headline coincidental-match bug -------------------------------

_ALMORAVID = (
    "The Almoravid dynasty was a Berber Muslim dynasty centered in Morocco and "
    "the western Maghreb. It established an empire in the 11th century that lasted "
    "about 6 generations before its decline and fall in the mid-12th century."
)


def test_almoravid_coincidental_block():
    """A knot crossing-number value 6 appears only as 'about 6 generations' in an
    unrelated dynasty article → the gate refuses it. (The deterministic subject
    pre-filter alone rejects it; the real backend is present to prove the
    end-to-end gate never returns 6.)"""
    claim = _claim(ClaimKind.NUMERIC, "the trefoil knot has crossing number 6")
    src = _prose(_ALMORAVID, title="Almoravid dynasty")
    assert prose_substantiated(
        "6", src, claim, backend=DartmouthBackend(), model=None, repo_root=None
    ) is False


# --- SC-004 : a genuinely-supporting prose source grounds the value -------------

_FRANCE = (
    "France, officially the French Republic, is a country in Western Europe. "
    "Its capital and largest city is Paris, which is also its political and "
    "cultural center."
)


def test_paris_grounded_kept():
    claim = _claim(ClaimKind.ENTITY_FACT, "the capital of France is Paris")
    src = _prose(_FRANCE, title="France")
    assert prose_substantiated(
        "Paris", src, claim, backend=DartmouthBackend(), model=None, repo_root=None
    ) is True


# --- SC-005 : a contradicting source never grounds the wrong value --------------

_AUSTRALIA = (
    "Canberra is the capital city of Australia. Although Sydney is the country's "
    "largest and oldest city, it is not the national capital; the seat of "
    "government is Canberra."
)


def test_sydney_contradicted_not_grounded():
    claim = _claim(ClaimKind.ENTITY_FACT, "the capital of Australia is Sydney")
    src = _prose(_AUSTRALIA, title="Australia")
    # 'Sydney' is locatable and the subject keywords co-occur, so the deterministic
    # pre-filter passes and the LIVE entailment call is what rejects it.
    assert prose_substantiated(
        "Sydney", src, claim, backend=DartmouthBackend(), model=None, repo_root=None
    ) is False


# --- SC-006 : bound claim blocked before any fetch (real backend available) -----


def test_bound_claim_blocked_before_fetch():
    claim = _claim(ClaimKind.NUMERIC, "the crossing number is ≤ 6 for this knot")
    result = fill_claim(claim, backend=DartmouthBackend(), model=None)
    assert result.status == "blocked"
    assert result.channels_tried == []  # no fetch happened


# --- SC-002/SC-003 (by construction) : STRUCTURED channels skip the prose gate --


def test_structured_channel_skips_prose_gate():
    """An OEIS (STRUCTURED) candidate is admitted on literal presence alone — the
    prose semantic gate is not applied (subject<->value link is inherent). This
    is the no-regression guarantee for the exact-count path; the full live
    9988/π fills are exercised by the offline integration suites."""
    claim = _claim(ClaimKind.NUMERIC, "prime knots at 13 crossings number 9988")
    src = FetchedSource(
        channel="oeis", source_id="A002863", url="https://oeis.org/A002863",
        title=None, text="13 9988\n14 46972", authority=1,
    )
    assert is_structured("oeis")
    assert _accept(
        "9988", src, claim, backend=DartmouthBackend(), model=None, repo_root=None
    ) is True
