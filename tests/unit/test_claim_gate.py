"""T009 — unit tests for claims/gate.py (spec 016 foundational)."""

from __future__ import annotations

from llmxive.claims.gate import (
    CLAIM_MARKER_PREFIX,
    find_unresolved_claims,
    has_unresolved_claims,
    mark_unresolved,
)
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id


def _make_claim(cid: str = "c_deadbeef") -> Claim:
    return Claim(
        claim_id=cid,
        kind=ClaimKind.NUMERIC,
        raw_text="99",
        canonical="x=99",
        context="ctx",
        artifact_path="projects/PROJ-001/specs/spec.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


class TestClaimMarkerPrefix:
    def test_exact_value(self):
        assert CLAIM_MARKER_PREFIX == "[UNRESOLVED-CLAIM:"


class TestMarkUnresolved:
    def test_appends_marker_to_text(self):
        c = _make_claim()
        result = mark_unresolved("The value is 99.", c, "no citable source")
        assert CLAIM_MARKER_PREFIX in result
        assert c.claim_id in result

    def test_includes_reason(self):
        c = _make_claim()
        result = mark_unresolved("text", c, "no citable source")
        assert "no citable source" in result

    def test_result_is_string(self):
        c = _make_claim()
        result = mark_unresolved("text", c, "reason")
        assert isinstance(result, str)


class TestHasUnresolvedClaims:
    def test_true_when_marker_present(self):
        text = "Something [UNRESOLVED-CLAIM: c_deadbeef — no source] here."
        assert has_unresolved_claims(text) is True

    def test_false_when_no_marker(self):
        text = "Clean text with no markers."
        assert has_unresolved_claims(text) is False

    def test_false_on_empty_string(self):
        assert has_unresolved_claims("") is False

    def test_true_after_mark_unresolved(self):
        c = _make_claim()
        marked = mark_unresolved("value is 99", c, "reason")
        assert has_unresolved_claims(marked) is True


class TestFindUnresolvedClaims:
    def test_returns_empty_list_when_clean(self):
        text = "No markers here."
        assert find_unresolved_claims(text) == []

    def test_returns_one_body(self):
        text = "Something [UNRESOLVED-CLAIM: c_deadbeef — no source] here."
        bodies = find_unresolved_claims(text)
        assert len(bodies) == 1
        assert "c_deadbeef" in bodies[0]

    def test_returns_multiple_bodies(self):
        text = (
            "A [UNRESOLVED-CLAIM: c_aaaaaaaa — reason1] and "
            "B [UNRESOLVED-CLAIM: c_bbbbbbbb — reason2]."
        )
        bodies = find_unresolved_claims(text)
        assert len(bodies) == 2

    def test_after_mark_unresolved_body_contains_id(self):
        c = _make_claim("c_deadbeef")
        marked = mark_unresolved("value 99", c, "test reason")
        bodies = find_unresolved_claims(marked)
        assert len(bodies) >= 1
        assert any("c_deadbeef" in b for b in bodies)

    def test_returns_bodies_not_full_marker(self):
        text = "[UNRESOLVED-CLAIM: my-body-text]"
        bodies = find_unresolved_claims(text)
        assert bodies[0] == "my-body-text"
