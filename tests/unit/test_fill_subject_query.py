"""T005 — unit tests for fill/subject_query.py (pure, no backend)."""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.subject_query import strip_asserted_value, subject_query

# ---------------------------------------------------------------------------
# strip_asserted_value — pure, deterministic
# ---------------------------------------------------------------------------


class TestStripAssertedValue:
    def test_removes_number_with_comma(self):
        text = "For crossing number 13, the exact count is 27,635 prime knots"
        result = strip_asserted_value(text, "27635")
        assert "27,635" not in result
        assert "27635" not in result
        # Subject and qualifiers preserved
        assert "prime knots" in result
        assert "crossing number 13" in result

    def test_removes_number_without_comma(self):
        text = "There are 27635 prime knots at crossing number 13"
        result = strip_asserted_value(text, "27635")
        assert "27635" not in result
        assert "prime knots" in result

    def test_removes_number_with_space_thousands(self):
        text = "There are 27 635 prime knots at crossing number 13"
        result = strip_asserted_value(text, "27635")
        assert "27 635" not in result
        assert "prime knots" in result

    def test_value_already_formatted_with_comma(self):
        # Passing the comma-formatted version as value also works
        text = "For crossing number 13, the exact count is 27,635 prime knots"
        result = strip_asserted_value(text, "27,635")
        assert "27,635" not in result
        assert "prime knots" in result
        assert "crossing number 13" in result

    def test_none_value_returns_text_unchanged(self):
        text = "some text with a claim"
        result = strip_asserted_value(text, None)
        assert result == text

    def test_empty_value_returns_text_unchanged(self):
        text = "some text with a claim"
        result = strip_asserted_value(text, "")
        assert result == text

    def test_unrelated_text_untouched(self):
        # A number appearing elsewhere that is NOT the value is left intact
        text = "At crossing number 13, there are 27,635 prime knots"
        result = strip_asserted_value(text, "27635")
        assert "13" in result  # crossing number 13 untouched

    def test_strips_decimal_variants(self):
        text = "The value is 3.14159 approximately"
        result = strip_asserted_value(text, "3.14159")
        assert "3.14159" not in result
        assert "approximately" in result

    def test_strips_value_from_middle(self):
        text = "prime knots 9988 at 13 crossings"
        result = strip_asserted_value(text, "9988")
        assert "9988" not in result
        assert "prime knots" in result
        assert "13 crossings" in result

    def test_idempotent(self):
        text = "There are 27,635 prime knots"
        once = strip_asserted_value(text, "27635")
        twice = strip_asserted_value(once, "27635")
        assert once == twice


# ---------------------------------------------------------------------------
# subject_query — pure fallback (no backend)
# ---------------------------------------------------------------------------


def _make_claim(raw_text: str, canonical: str = "", resolved_value: str | None = None) -> Claim:
    return Claim(
        claim_id="c_test",
        kind=ClaimKind.NUMERIC,
        raw_text=raw_text,
        canonical=canonical or raw_text,
        context="test context",
        artifact_path="test.md",
        source_type="external",
        status=ClaimStatus.NOT_ENOUGH_INFO,
        resolved_value=resolved_value,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-01-01T00:00:00Z",
    )


class TestSubjectQuery:
    def test_no_backend_strips_value(self):
        claim = _make_claim(
            raw_text="There are 27,635 prime knots at crossing number 13",
            resolved_value="27635",
        )
        q = subject_query(claim, backend=None)
        assert "27,635" not in q
        assert "27635" not in q
        assert "prime knots" in q

    def test_no_backend_no_resolved_value_returns_raw_text(self):
        claim = _make_claim(
            raw_text="prime knots at crossing number 13",
            resolved_value=None,
        )
        q = subject_query(claim, backend=None)
        # Without a value to strip, the raw text (or canonical) is returned as-is
        assert "prime knots" in q

    def test_backend_none_returns_str(self):
        claim = _make_claim("some numeric claim", resolved_value="42")
        q = subject_query(claim, backend=None, model=None, repo_root=None)
        assert isinstance(q, str)
        assert len(q) > 0
