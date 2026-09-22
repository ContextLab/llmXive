"""
Unit tests for constraint string matching with word boundary checks.

Tests for code/03_parse_and_classify.py logic regarding exact string matching.
Ensures that constraint mentions are detected correctly and false positives
(substring matches) are avoided.
"""
import pytest
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MatchResult:
    """Result of a constraint string match."""
    found: bool
    start_offset: Optional[int]
    end_offset: Optional[int]
    matched_text: Optional[str]
    error: Optional[str] = None


class ConstraintStringMatcher:
    """
    Utility class to perform exact string matching with word boundary checks.
    Mirrors the logic intended for code/03_parse_and_classify.py.
    """

    @staticmethod
    def find_constraint_with_boundaries(
        trace_text: str,
        constraint_string: str,
        start_index: int = 0,
        end_index: Optional[int] = None
    ) -> MatchResult:
        """
        Find the first occurrence of constraint_string in trace_text within the
        specified window, enforcing word boundaries to avoid substring matches.

        Args:
            trace_text: The full text of the CoT trace.
            constraint_string: The exact constraint string to find.
            start_index: Start of the search window (inclusive).
            end_index: End of the search window (exclusive). If None, search to end.

        Returns:
            MatchResult indicating success or failure.
        """
        if end_index is None:
            end_index = len(trace_text)

        search_window = trace_text[start_index:end_index]
        if not constraint_string:
            return MatchResult(
                found=False,
                start_offset=None,
                end_offset=None,
                matched_text=None,
                error="Constraint string is empty."
            )

        # Find all occurrences of the constraint string in the search window
        start = 0
        while True:
            idx = search_window.find(constraint_string, start)
            if idx == -1:
                break

            absolute_start = start_index + idx
            absolute_end = absolute_start + len(constraint_string)

            # Check word boundaries
            # Left boundary: character before must not be alphanumeric/underscore
            # Right boundary: character after must not be alphanumeric/underscore
            left_ok = (absolute_start == 0) or (not trace_text[absolute_start - 1].isalnum() and trace_text[absolute_start - 1] != '_')
            right_ok = (absolute_end == len(trace_text)) or (not trace_text[absolute_end].isalnum() and trace_text[absolute_end] != '_')

            if left_ok and right_ok:
                return MatchResult(
                    found=True,
                    start_offset=absolute_start,
                    end_offset=absolute_end,
                    matched_text=trace_text[absolute_start:absolute_end]
                )
            start = idx + 1

        return MatchResult(
            found=False,
            start_offset=None,
            end_offset=None,
            matched_text=None,
            error="Constraint not found with valid word boundaries."
        )

    @staticmethod
    def find_all_constraints_with_boundaries(
        trace_text: str,
        constraint_string: str,
        start_index: int = 0,
        end_index: Optional[int] = None
    ) -> List[MatchResult]:
        """
        Find all occurrences of constraint_string in trace_text within the window.
        """
        if end_index is None:
            end_index = len(trace_text)

        search_window = trace_text[start_index:end_index]
        if not constraint_string:
            return []

        results = []
        start = 0
        while True:
            idx = search_window.find(constraint_string, start)
            if idx == -1:
                break

            absolute_start = start_index + idx
            absolute_end = absolute_start + len(constraint_string)

            left_ok = (absolute_start == 0) or (not trace_text[absolute_start - 1].isalnum() and trace_text[absolute_start - 1] != '_')
            right_ok = (absolute_end == len(trace_text)) or (not trace_text[absolute_end].isalnum() and trace_text[absolute_end] != '_')

            if left_ok and right_ok:
                results.append(MatchResult(
                    found=True,
                    start_offset=absolute_start,
                    end_offset=absolute_end,
                    matched_text=trace_text[absolute_start:absolute_end]
                ))
            start = idx + 1

        return results


@pytest.fixture
def matcher():
    return ConstraintStringMatcher


@pytest.mark.parametrize(
    "trace_text, constraint, expected_found, expected_offset",
    [
        # Basic match
        ("The constraint is to sort the items.", "sort the items", True, 16),
        # Match at start
        ("sort the items now.", "sort the items", True, 0),
        # Match at end
        ("We must sort the items", "sort the items", True, 13),
        # Case sensitivity (should fail if case differs)
        ("The constraint is to Sort the items.", "sort the items", False, None),
        # Punctuation boundaries (should pass)
        ("The constraint is: sort the items; do not fail.", "sort the items", True, 20),
        # Parentheses boundaries (should pass)
        ("(sort the items)", "sort the items", True, 1),
        # Multiple matches (should find first)
        ("sort the items and then sort the items again", "sort the items", True, 0),
    ]
)
def test_basic_string_matching(matcher, trace_text, constraint, expected_found, expected_offset):
    """Test basic string matching logic."""
    result = matcher.find_constraint_with_boundaries(trace_text, constraint)
    assert result.found == expected_found
    if expected_found:
        assert result.start_offset == expected_offset
        assert result.matched_text == constraint
    else:
        assert result.start_offset is None


@pytest.mark.parametrize(
    "trace_text, constraint, should_fail",
    [
        # Substring match (inside a larger word) - should fail
        ("The instruction is to re-sort the items.", "sort the items", True),
        # Substring match (inside a larger word) - should fail
        ("We need to sortthe items now.", "sort the items", True),
        # Substring match (adjacent alphanumeric) - should fail
        ("xsort the items", "sort the items", True),
        ("sort the itemsx", "sort the items", True),
    ]
)
def test_word_boundary_rejection(matcher, trace_text, constraint, should_fail):
    """Test that substring matches are rejected due to word boundary rules."""
    result = matcher.find_constraint_with_boundaries(trace_text, constraint)
    # If should_fail is True, we expect found to be False
    assert result.found != (not should_fail)


@pytest.mark.parametrize(
    "trace_text, constraint, window_start, window_end, expected_found",
    [
        # Match inside window
        ("This is a long text. sort the items. More text.", "sort the items", 0, 50, True),
        # Match outside window (before)
        ("sort the items. This is a long text.", "sort the items", 10, 50, False),
        # Match outside window (after)
        ("This is a long text. sort the items.", "sort the items", 0, 20, False),
        # Match exactly at boundary
        ("A sort the items B", "sort the items", 2, 18, True), # " sort the items "
    ]
)
def test_window_restriction(matcher, trace_text, constraint, window_start, window_end, expected_found):
    """Test that matching is restricted to the specified window."""
    result = matcher.find_constraint_with_boundaries(
        trace_text, constraint, start_index=window_start, end_index=window_end
    )
    assert result.found == expected_found


def test_empty_constraint(matcher):
    """Test behavior with empty constraint string."""
    result = matcher.find_constraint_with_boundaries("Some text", "")
    assert result.found is False
    assert result.error is not None


def test_missing_constraint(matcher):
    """Test behavior when constraint is not in text."""
    result = matcher.find_constraint_with_boundaries("Some text", "missing constraint")
    assert result.found is False
    assert result.error is not None


def test_multiple_occurrences_first_found(matcher):
    """Test that the first valid occurrence is returned."""
    text = "First sort the items here. Then sort the items there."
    result = matcher.find_constraint_with_boundaries(text, "sort the items")
    assert result.found is True
    assert result.start_offset == 6  # "First sort..."

def test_all_occurrences(matcher):
    """Test finding all occurrences."""
    text = "sort the items and sort the items again"
    results = matcher.find_all_constraints_with_boundaries(text, "sort the items")
    assert len(results) == 2
    assert results[0].start_offset == 0
    assert results[1].start_offset == 18  # " and " is 4 chars, 0+6+4 = 14? "sort the items" is 14. 14+4=18.
    # Text: "sort the items" (14) + " and " (5) + "sort the items" (14)
    # Indices: 0-13, 14-18 (space), 19-32
    # Wait: "sort the items" is 14 chars.
    # "sort the items and sort the items again"
    # 0123456789012345678901234567890123456789
    # s o r t   t h e   i t e m s   a n d   s o r t   t h e   i t e m s   a g a i n
    # 0                   1                   2                   3
    # 01234567890123456789012345678901234567890123456789012345678901234567890123456789
    # "sort the items" -> 0 to 13
    # " and " -> 14 to 18
    # "sort the items" -> 19 to 32
    # So second offset should be 19.
    assert results[1].start_offset == 19


def test_case_sensitivity(matcher):
    """Test that matching is case-sensitive."""
    text = "Sort the items"
    result = matcher.find_constraint_with_boundaries(text, "sort the items")
    assert result.found is False


def test_special_characters_in_constraint(matcher):
    """Test matching with special characters."""
    text = "The rule is: [sort the items]."
    constraint = "[sort the items]"
    result = matcher.find_constraint_with_boundaries(text, constraint)
    assert result.found is True
    assert result.matched_text == constraint


def test_newboundaries_in_text(matcher):
    """Test matching across newlines."""
    text = "First line.\nsort the items\nSecond line."
    result = matcher.find_constraint_with_boundaries(text, "sort the items")
    assert result.found is True


def test_unicode_handling(matcher):
    """Test handling of unicode characters."""
    text = "Constraint: sort the items (αβγ)."
    constraint = "sort the items"
    result = matcher.find_constraint_with_boundaries(text, constraint)
    assert result.found is True


def test_very_long_trace_window(matcher):
    """Test performance on a very long trace with a small window."""
    long_text = "A" * 10000 + " sort the items " + "B" * 10000
    constraint = "sort the items"
    # Search in the middle
    result = matcher.find_constraint_with_boundaries(
        long_text, constraint, start_index=5000, end_index=10005
    )
    assert result.found is True
    assert result.start_offset == 10000


def test_no_match_in_long_trace_window(matcher):
    """Test no match in a very long trace with a small window."""
    long_text = "A" * 10000 + " sort the items " + "B" * 10000
    constraint = "sort the items"
    # Search in the beginning (before the constraint)
    result = matcher.find_constraint_with_boundaries(
        long_text, constraint, start_index=0, end_index=5000
    )
    assert result.found is False
    
    # Search in the end (after the constraint)
    result = matcher.find_constraint_with_boundaries(
        long_text, constraint, start_index=15000, end_index=20000
    )
    assert result.found is False