"""
Unit tests for the heuristics utilities.
These tests verify the technical token ratio calculation and the composite
semantic density computation as defined by FR-008:
    density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio
The tests use the real implementation from `code/utils/heuristics.py`.
"""

import sys
import pytest
from pathlib import Path

# Ensure the project root is on the import path for sibling modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.heuristics import (
    calculate_technical_token_ratio,
    calculate_composite_density,
)
from utils.entropy import entropy_per_token


class TestCalculateTechnicalTokenRatio:
    """Tests for the calculate_technical_token_ratio function."""

    def test_no_technical_terms(self):
        """Text with no technical terms should return 0.0."""
        text = "this is a simple sentence with no special terms"
        terms = {"search_context", "retrieval_window"}
        result = calculate_technical_token_ratio(text, terms)
        assert result == 0.0

    def test_all_technical_terms(self):
        """Text with only technical terms should return 1.0."""
        text = "search_context retrieval_window"
        terms = {"search_context", "retrieval_window"}
        result = calculate_technical_token_ratio(text, terms)
        assert result == 1.0

    def test_partial_match(self):
        """Text with partial technical terms should return correct ratio."""
        text = "search_context and some other words retrieval_window"
        terms = {"search_context", "retrieval_window"}
        # Tokens: ["search_context", "and", "some", "other", "words", "retrieval_window"]
        # Technical tokens: 2
        result = calculate_technical_token_ratio(text, terms)
        assert abs(result - (2 / 6)) < 1e-5

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""
        text = "SEARCH_CONTEXT retrieval_window"
        terms = {"search_context", "retrieval_window"}
        result = calculate_technical_token_ratio(text, terms)
        assert result == 1.0

    def test_empty_text(self):
        """Empty text should return 0.0."""
        result = calculate_technical_token_ratio("", {"term"})
        assert result == 0.0

    def test_empty_terms_set(self):
        """Empty terms set should return 0.0."""
        result = calculate_technical_token_ratio("any text", set())
        assert result == 0.0


class TestCalculateCompositeDensity:
    """Tests for the calculate_composite_density function."""

    def test_default_weights_low_entropy_full_tech(self):
        """
        Low‑entropy text where every token is a technical term.
        Expected density = 0.6 * 0.0 + 0.4 * 1.0 = 0.4
        """
        text = "aaaa"  # repeated character → entropy 0.0
        terms = ["aaaa"]  # make the single token a technical term
        density = calculate_composite_density(text, terms)
        assert abs(density - 0.4) < 1e-6

    def test_default_weights_mixed(self):
        """
        Text with two tokens, one technical and one non‑technical.
        Verify that the computed density matches the formula using
        the actual entropy_per_token value.
        """
        text = "foo bar"
        terms = ["foo"]  # only 'foo' is technical

        # Expected components
        expected_entropy = entropy_per_token(text)
        expected_ratio = calculate_technical_token_ratio(text, set(terms))

        expected_density = 0.6 * expected_entropy + 0.4 * expected_ratio

        density = calculate_composite_density(text, terms)
        assert abs(density - expected_density) < 1e-6

    def test_zero_entropy_and_zero_tech_ratio(self):
        """
        Text with zero entropy and no technical terms.
        Expected density = 0.0
        """
        text = "bbbbbbbbbb"  # single repeated character → entropy 0.0
        terms = []  # no technical terms

        density = calculate_composite_density(text, terms)
        assert density == 0.0

    def test_non_string_input_raises(self):
        """
        The function expects a string; passing a non‑string should raise an error
        from the underlying entropy calculation.
        """
        with pytest.raises(TypeError):
            # Pass an integer instead of a string
            calculate_composite_density(12345, [])