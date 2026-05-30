"""T013: Unit tests for fill/channels/oeis.py — pure parsers only.

Real-call parts (fetch_bfile) are gated behind LLMXIVE_REAL_TESTS.
"""

from __future__ import annotations

import os

import pytest

from llmxive.fill.channels.oeis import a_numbers_in, _parse_bfile


# ---------------------------------------------------------------------------
# a_numbers_in — pure regex extractor
# ---------------------------------------------------------------------------

class TestANumbersIn:
    def test_single(self):
        assert a_numbers_in("see OEIS A002863 for details") == ["A002863"]

    def test_multiple(self):
        result = a_numbers_in("A002863 counts prime knots; A000001 counts groups")
        assert result == ["A002863", "A000001"]

    def test_dedup_order_preserving(self):
        result = a_numbers_in("A002863 and again A002863 then A000001")
        assert result == ["A002863", "A000001"]

    def test_empty_string(self):
        assert a_numbers_in("") == []

    def test_no_a_numbers(self):
        assert a_numbers_in("There are 9988 prime knots at 13 crossings.") == []

    def test_six_digit(self):
        assert a_numbers_in("See A000001 for small groups") == ["A000001"]

    def test_seven_digit(self):
        assert a_numbers_in("Reference: A1234567") == ["A1234567"]

    def test_five_digit_not_matched(self):
        # Must be ≥6 digits
        assert a_numbers_in("See A12345 for more") == []

    def test_embedded_in_punctuation(self):
        result = a_numbers_in("(A002863), [A000001].")
        assert result == ["A002863", "A000001"]


# ---------------------------------------------------------------------------
# _parse_bfile — pure b-file text parser
# ---------------------------------------------------------------------------

class TestParseBfile:
    def test_basic(self):
        text = "13 9988\n14 46972\n"
        assert _parse_bfile(text) == {13: 9988, 14: 46972}

    def test_skip_comments(self):
        text = "# comment line\n13 9988\n14 46972\n"
        assert _parse_bfile(text) == {13: 9988, 14: 46972}

    def test_skip_blank_lines(self):
        text = "\n13 9988\n\n14 46972\n"
        assert _parse_bfile(text) == {13: 9988, 14: 46972}

    def test_empty(self):
        assert _parse_bfile("") == {}

    def test_only_comments(self):
        assert _parse_bfile("# nothing here\n# more comments\n") == {}

    def test_negative_index(self):
        text = "0 1\n1 1\n2 2\n"
        assert _parse_bfile(text) == {0: 1, 1: 1, 2: 2}

    def test_large_values(self):
        text = "13 9988\n"
        result = _parse_bfile(text)
        assert result[13] == 9988

    def test_inline_comment_not_parsed(self):
        # Lines with inline comments after values are unusual in b-files;
        # we only split on first two tokens (index, value)
        text = "13 9988\n"
        assert _parse_bfile(text) == {13: 9988}


# ---------------------------------------------------------------------------
# fetch_bfile — real network (gated)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="LLMXIVE_REAL_TESTS not set",
)
def test_fetch_bfile_a002863_real():
    from llmxive.fill.channels.oeis import fetch_bfile

    result = fetch_bfile("A002863")
    assert isinstance(result, dict), "fetch_bfile should return a dict"
    assert result.get(13) == 9988, f"A002863[13] should be 9988, got {result.get(13)}"
    assert result.get(14) == 46972, f"A002863[14] should be 46972, got {result.get(14)}"
