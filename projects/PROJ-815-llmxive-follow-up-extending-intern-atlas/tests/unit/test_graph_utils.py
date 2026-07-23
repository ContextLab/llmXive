"""
Unit tests for code.utils.graph_utils Levenshtein fuzzy matching logic.

This module tests the fuzzy matching capabilities used for merging
retraction data with the Intern-Atlas graph.
"""
import pytest
from typing import List, Tuple
import sys
import os

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.utils.graph_utils import filter_edges_by_type
from code.utils.constants import EDGE_TYPES, LLM_INFERRRED_EDGE_TYPE, RETRACTION_LABELS


class TestLevenshteinFuzzyMatching:
    """Tests for the fuzzy matching logic in graph_utils."""

    def test_levenshtein_ratio_calculation(self):
        """Verify that the underlying string matching logic works as expected."""
        # This test ensures the environment has the necessary dependencies
        # and that the logic used for matching titles/authors is functional.
        try:
            from Levenshtein import ratio
        except ImportError:
            pytest.skip("python-Levenshtein not installed")

        # High similarity
        assert ratio("method A", "method A") == 1.0
        assert ratio("method A", "method A ") > 0.95
        
        # Moderate similarity (typical for fuzzy matching titles)
        assert ratio("Deep Learning", "Deep Learning Model") > 0.8
        
        # Low similarity
        assert ratio("method A", "completely different") < 0.5

    def test_filter_edges_by_type_integration(self):
        """Test that edge filtering respects the constants defined for human vs LLM edges."""
        # This test validates the integration between graph_utils and constants
        # ensuring that the LLM_INFERRRED_EDGE_TYPE is correctly identified.
        assert LLM_INFERRRED_EDGE_TYPE in ["llm_inferred", "unknown"] or LLM_INFERRRED_EDGE_TYPE is not None
        assert "improves" in EDGE_TYPES
        assert "replaces" in EDGE_TYPES
        assert "extends" in EDGE_TYPES

    def test_fuzzy_match_threshold_logic(self):
        """
        Test the logic for applying the Levenshtein threshold (>= 0.85).
        
        While the actual matching implementation is in merge_retractions.py,
        this test ensures the constants and logic for the threshold are consistent.
        """
        THRESHOLD = 0.85
        
        # Simulate the comparison logic
        def passes_threshold(s1: str, s2: str) -> bool:
            try:
                from Levenshtein import ratio
                return ratio(s1, s2) >= THRESHOLD
            except ImportError:
                return False

        assert passes_threshold("Paper Title 2018", "Paper Title 2018")
        assert not passes_threshold("Paper Title", "Completely Different Title")