"""
Unit tests for heuristics.py utility functions.
Verifies technical token ratio calculation and config file loading.
"""
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.heuristics import calculate_technical_token_ratio, calculate_composite_density


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
        # Total tokens: "search_context", "and", "some", "other", "words", "retrieval_window" = 6
        # Technical: 2
        # Ratio: 2/6 = 0.333...
        result = calculate_technical_token_ratio(text, terms)
        assert abs(result - 1/3) < 1e-5

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

    def test_weighted_sum(self):
        """Composite density should be a weighted sum of entropy and technical ratio."""
        # Mock values
        entropy_val = 0.5
        tech_ratio = 0.6
        alpha = 0.7
        beta = 0.3

        result = calculate_composite_density(entropy_val, tech_ratio, alpha, beta)
        expected = alpha * entropy_val + beta * tech_ratio
        assert abs(result - expected) < 1e-5

    def test_weights_sum_to_one(self):
        """Test with weights that sum to 1.0."""
        entropy_val = 0.8
        tech_ratio = 0.4
        alpha = 0.5
        beta = 0.5

        result = calculate_composite_density(entropy_val, tech_ratio, alpha, beta)
        expected = 0.5 * 0.8 + 0.5 * 0.4
        assert abs(result - expected) < 1e-5

    def test_default_weights(self):
        """Test with default weights (0.5, 0.5)."""
        entropy_val = 0.6
        tech_ratio = 0.4

        result = calculate_composite_density(entropy_val, tech_ratio)
        expected = 0.5 * 0.6 + 0.5 * 0.4
        assert abs(result - expected) < 1e-5

    def test_zero_entropy(self):
        """Zero entropy should still contribute correctly."""
        entropy_val = 0.0
        tech_ratio = 0.8
        alpha = 0.5
        beta = 0.5

        result = calculate_composite_density(entropy_val, tech_ratio, alpha, beta)
        expected = 0.5 * 0.0 + 0.5 * 0.8
        assert abs(result - expected) < 1e-5

    def test_zero_tech_ratio(self):
        """Zero technical ratio should still contribute correctly."""
        entropy_val = 0.9
        tech_ratio = 0.0
        alpha = 0.5
        beta = 0.5

        result = calculate_composite_density(entropy_val, tech_ratio, alpha, beta)
        expected = 0.5 * 0.9 + 0.5 * 0.0
        assert abs(result - expected) < 1e-5
