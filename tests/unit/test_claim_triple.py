"""T030 — Unit tests for claims/triple.py pure helpers (no mocks, no IO).

Tests:
- decompose_triple: correct SPO parsing for several representative strings.
- check_ordering: correctly accepts and rejects ordering claims over real lists.
"""

from __future__ import annotations

import pytest

from llmxive.claims.triple import check_ordering, decompose_triple


class TestDecomposeTriple:
    """Pure SPO parsing — no IO, no backends."""

    def test_author_of(self):
        subj, rel, obj = decompose_triple("Gauss is the author of Disquisitiones")
        assert "gauss" in subj.lower()
        assert "author of" in rel.lower()
        assert "disquisitiones" in obj.lower()

    def test_capital_of(self):
        subj, rel, obj = decompose_triple("Paris is the capital of France")
        assert "paris" in subj.lower()
        assert "capital of" in rel.lower()
        assert "france" in obj.lower()

    def test_wrote(self):
        subj, rel, obj = decompose_triple("Shakespeare wrote Hamlet")
        assert "shakespeare" in subj.lower()
        assert "wrote" in rel.lower()
        assert "hamlet" in obj.lower()

    def test_canonical_separator_form(self):
        """'|' separated canonical triple form."""
        subj, rel, obj = decompose_triple("Gauss | author of | Disquisitiones")
        assert subj.strip() == "Gauss"
        assert rel.strip() == "author of"
        assert obj.strip() == "Disquisitiones"

    def test_invented_by(self):
        subj, rel, obj = decompose_triple("The telephone was invented by Bell")
        assert "bell" in obj.lower() or "bell" in subj.lower()
        assert rel != ""

    def test_located_in(self):
        subj, rel, obj = decompose_triple("The Eiffel Tower is located in Paris")
        assert "eiffel" in subj.lower()
        assert "located in" in rel.lower()
        assert "paris" in obj.lower()

    def test_founded_by(self):
        subj, rel, obj = decompose_triple("Apple was founded by Steve Jobs")
        assert "apple" in subj.lower()
        assert "founded by" in rel.lower()
        assert "jobs" in obj.lower()

    def test_returns_triple_always(self):
        """Even with no recognizable relation, returns a 3-tuple (never raises)."""
        result = decompose_triple("some random text with no relation")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_empty_string(self):
        result = decompose_triple("")
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestCheckOrdering:
    """Pure ordering check — no IO, no backends."""

    # --- largest / greatest ---

    def test_largest_correct(self):
        """Jupiter is correctly identified as largest (largest mass)."""
        candidates = [
            ("Jupiter", 1.898e27),
            ("Saturn", 5.683e26),
            ("Earth", 5.972e24),
            ("Mars", 6.39e23),
        ]
        assert check_ordering(candidates, "Jupiter is the largest planet") is True

    def test_largest_wrong(self):
        """Earth is NOT the largest planet by mass."""
        candidates = [
            ("Earth", 5.972e24),
            ("Jupiter", 1.898e27),
            ("Saturn", 5.683e26),
        ]
        assert check_ordering(candidates, "Earth is the largest planet") is False

    def test_largest_simple_numbers(self):
        """Works with plain numeric lists (no labels)."""
        assert check_ordering([100, 50, 30, 10], "100 is the largest") is True
        assert check_ordering([30, 100, 50], "30 is the largest") is False

    # --- smallest ---

    def test_smallest_correct(self):
        candidates = [
            ("Mercury", 3.285e23),
            ("Venus", 4.867e24),
            ("Earth", 5.972e24),
        ]
        assert check_ordering(candidates, "Mercury is the smallest") is True

    def test_smallest_wrong(self):
        candidates = [
            ("Earth", 5.972e24),
            ("Mercury", 3.285e23),
            ("Venus", 4.867e24),
        ]
        assert check_ordering(candidates, "Earth is the smallest") is False

    # --- highest / lowest ---

    def test_highest_correct(self):
        assert check_ordering([8849, 8611, 8586], "8849 is the highest") is True

    def test_lowest_correct(self):
        assert check_ordering([1, 5, 10], "1 is the lowest") is True

    def test_lowest_wrong(self):
        assert check_ordering([10, 1, 5], "10 is the lowest") is False

    # --- earliest ---

    def test_earliest_correct(self):
        """Earliest year = smallest number."""
        candidates = [("Gutenberg", 1450), ("Newton", 1687), ("Darwin", 1859)]
        assert check_ordering(candidates, "Gutenberg is the earliest") is True

    def test_earliest_wrong(self):
        candidates = [("Darwin", 1859), ("Gutenberg", 1450), ("Newton", 1687)]
        assert check_ordering(candidates, "Darwin is the earliest") is False

    # --- edge cases ---

    def test_single_candidate_vacuously_true(self):
        """One item — nothing to compare against."""
        assert check_ordering([("Jupiter", 1.898e27)], "Jupiter is largest") is True

    def test_empty_list_vacuously_true(self):
        assert check_ordering([], "something is largest") is True

    def test_unknown_direction_conservative_false(self):
        """Unrecognized superlative keyword → conservative False."""
        assert check_ordering([10, 5, 3], "10 is the middlemost") is False

    def test_string_numbers_parsed(self):
        """String-formatted numbers with commas are parsed correctly."""
        candidates = [("A", "9,988"), ("B", "1,000"), ("C", "500")]
        assert check_ordering(candidates, "A is the largest") is True
        candidates2 = [("B", "1,000"), ("A", "9,988"), ("C", "500")]
        assert check_ordering(candidates2, "B is the largest") is False
