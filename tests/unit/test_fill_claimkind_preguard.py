"""Unit tests for the fill claim-kind pre-guard (spec 019, C5 / US3).

A NUMERIC claim asserting an INEQUALITY bound (≤ ≥ < >) or a PERCENTAGE, or a
digit-less NUMERIC claim, is not a fillable point-valued fact. ``fill_claim`` MUST
refuse it BEFORE any network fetch (Fail Fast), returning a ``blocked`` result
with ``channels_tried == []`` (nothing was fetched). Approximation markers (~ ≈)
must NOT be blocked — they route to the spec-018 approximate path.

The blocked cases return at the pre-guard before any backend/network use, so we
pass ``backend=None`` and assert ``channels_tried == []`` (the no-fetch signal).
The proceed path (a normal point-valued claim is NOT short-circuited) is asserted
at the predicate level here (network-free) and end-to-end by the real_call suite.
"""

from __future__ import annotations

import pytest

from llmxive.claims.canonical import (
    _asserted_is_inequality_or_percent,
    _asserted_value,
)
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.service import fill_claim


def _numeric_claim(raw: str) -> Claim:
    return Claim(
        claim_id="c", kind=ClaimKind.NUMERIC, raw_text=raw, canonical=raw,
        context="knot theory", artifact_path="specs/x/spec.md",
        source_type="external", status=ClaimStatus.PENDING, resolved_value=None,
        evidence=None, resolver=None, attempts=0, updated_at="2026-06-02T00:00:00Z",
    )


@pytest.mark.parametrize(
    "raw",
    [
        "the crossing number is ≤6",          # adjacent inequality (the PROJ-552 bug)
        "the crossing number is ≤ 6",          # spaced inequality
        "the count is > 100 prime knots",       # strict inequality
        "about 95% of these knots are chiral",  # percentage
    ],
)
def test_inequality_or_percent_blocked_no_fetch(raw: str) -> None:
    result = fill_claim(_numeric_claim(raw), backend=None)
    assert result.status == "blocked"
    assert result.channels_tried == []  # nothing fetched (Fail Fast)
    assert "inequality" in result.reason or "percent" in result.reason


def test_digitless_numeric_blocked_no_fetch() -> None:
    raw = "the braid index is ≤ the crossing number for most knots"
    result = fill_claim(_numeric_claim(raw), backend=None)
    assert result.status == "blocked"
    assert result.channels_tried == []
    assert "digit-less" in result.reason


def test_normal_point_value_not_preguarded() -> None:
    """A plain point-valued numeric claim is NOT short-circuited by the pre-guard
    (asserted value present, not an inequality/percent) — so fill_claim proceeds
    past the guard. Asserted network-free via the guard predicates; the full
    proceed/fetch path is covered by the real_call suite."""
    raw = "the trefoil knot has crossing number 3"
    asserted = _asserted_value(raw)
    assert asserted == "3"
    assert _asserted_is_inequality_or_percent(raw, asserted) is False


def test_exact_count_and_approximation_not_preguarded() -> None:
    """SC-002 / SC-003: an exact count (9,988) and an approximate constant
    (π ≈ 3.14159) are point values — the pre-guard must NOT block them."""
    for raw in [
        "there are 9,988 prime knots at crossing number 13",
        "π ≈ 3.14159",
    ]:
        asserted = _asserted_value(raw)
        assert asserted is not None
        assert _asserted_is_inequality_or_percent(raw, asserted) is False
