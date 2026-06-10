"""T009 — unit tests for claims/gate.py (spec 016 foundational)."""

from __future__ import annotations

from llmxive.claims.gate import (
    CLAIM_MARKER_PREFIX,
    find_unresolved_claims,
    has_unresolved_claims,
    mark_unresolved,
    strip_claim_artifacts,
)
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus


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


class TestStripClaimArtifacts:
    """Fix B — re-running the claim layer must not re-extract its own output."""

    def test_removes_marker_preserving_prose(self):
        text = (
            "There are 9988 prime knots. [UNRESOLVED-CLAIM: c_017129ae — "
            "subjective] The census is reputable."
        )
        out = strip_claim_artifacts(text)
        assert "[UNRESOLVED-CLAIM:" not in out
        assert "There are 9988 prime knots." in out
        assert "The census is reputable." in out

    def test_preserves_aligned_whitespace_when_nothing_removed(self):
        # A clean doc (no markers/pointers) must round-trip byte-for-byte — the
        # whitespace collapse exists only to tidy a removal, so running it on a
        # directory tree / ASCII table mangled the alignment (spec 020 real-test).
        tree = (
            "```text\n"
            "specs/020/\n"
            "├── plan.md              # This file\n"
            "│   ├── requirements.txt\n"
            "└── tasks.md             # Phase 2 output\n"
            "```\n"
        )
        assert strip_claim_artifacts(tree) == tree
        assert strip_claim_artifacts(tree, preserve_pointers=True) == tree

    def test_removes_stray_pointer(self):
        text = "The count is {{claim:c_3369e68a}} per the source."
        out = strip_claim_artifacts(text)
        assert "{{claim:" not in out
        assert "The count is per the source." in out

    def test_no_marker_no_change_except_spacing(self):
        text = "A clean sentence with no artifacts."
        assert strip_claim_artifacts(text) == text

    def test_idempotent(self):
        text = "Count 9988. [UNRESOLVED-CLAIM: c_aaaaaaaa — r] {{claim:c_bbbbbbbb}}"
        once = strip_claim_artifacts(text)
        twice = strip_claim_artifacts(once)
        assert once == twice
        assert "[UNRESOLVED-CLAIM:" not in once
        assert "{{claim:" not in once

    def test_preserves_newlines(self):
        text = "Line one.\n\nLine two [UNRESOLVED-CLAIM: c_cccccccc — r].\n\nLine three."
        out = strip_claim_artifacts(text)
        assert "\n\n" in out
        assert out.count("\n\n") == 2
