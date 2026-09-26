"""
Unit tests for correlation analysis functions, specifically focusing on
the Benjamini-Hochberg (BH) false discovery rate correction.

This module extends existing tests for auto-switch logic and correlation
calculations to include rigorous testing of the multiple hypothesis
correction mechanism required for User Story 2.
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats
from unittest.mock import patch, MagicMock
import logging

# Import the function under test from the project's analysis module
# Based on the provided API surface: code/src/analysis/correlation.py
try:
    from src.analysis.correlation import apply_benjamini_hochberg
except ImportError:
    # Fallback for environments where the path might be set differently,
    # though the prompt implies 'src' is on the path via conftest or env.
    from code.src.analysis.correlation import apply_benjamini_hochberg


class TestBenjaminiHochbergCorrection:
    """
    Test suite for the Benjamini-Hochberg (BH) FDR correction implementation.
    """

    def test_bh_correction_empty_input(self):
        """Test that BH correction handles empty lists gracefully."""
        p_values = []
        result = apply_benjamini_hochberg(p_values)
        assert len(result) == 0
        assert result == []

    def test_bh_correction_single_value(self):
        """Test BH correction with a single p-value."""
        p_values = [0.05]
        result = apply_benjamini_hochberg(p_values)
        # With m=1, adjusted p-value = p * 1 / 1 = p
        assert len(result) == 1
        assert np.isclose(result[0], 0.05)

    def test_bh_correction_monotonicity(self):
        """
        Test that the adjusted p-values are monotonically non-decreasing
        when sorted by original p-value.
        """
        # Create a set of p-values
        p_values = [0.01, 0.04, 0.03, 0.20, 0.15, 0.05]
        result = apply_benjamini_hochberg(p_values)

        # The BH procedure ensures that adjusted p-values are non-decreasing
        # when the original p-values are sorted.
        # We sort the results based on the original order to check monotonicity
        # relative to the sorted original p-values.
        
        # Pair original and adjusted
        paired = list(zip(p_values, result))
        # Sort by original p-value
        paired.sort(key=lambda x: x[0])
        
        adjusted_sorted = [x[1] for x in paired]
        
        # Check non-decreasing
        for i in range(len(adjusted_sorted) - 1):
            assert adjusted_sorted[i] <= adjusted_sorted[i+1], \
                f"Adjusted p-values must be non-decreasing: {adjusted_sorted}"

    def test_bh_correction_known_values(self):
        """
        Test BH correction against a known example.
        Example: p-values [0.01, 0.04, 0.03, 0.20]
        m = 4
        Sorted: 0.01, 0.03, 0.04, 0.20
        Rank 1: 0.01 * 4/1 = 0.04
        Rank 2: 0.03 * 4/2 = 0.06
        Rank 3: 0.04 * 4/3 = 0.0533...
        Rank 4: 0.20 * 4/4 = 0.20
        
        Now enforce monotonicity (cumulative min from bottom up):
        Rank 4: 0.20
        Rank 3: min(0.0533, 0.20) = 0.0533
        Rank 2: min(0.06, 0.0533) = 0.0533
        Rank 1: min(0.04, 0.0533) = 0.04
        
        Final adjusted (sorted): [0.04, 0.0533, 0.0533, 0.20]
        Map back to original order [0.01, 0.04, 0.03, 0.20]:
        0.01 -> 0.04
        0.04 -> 0.0533
        0.03 -> 0.0533
        0.20 -> 0.20
        """
        p_values = [0.01, 0.04, 0.03, 0.20]
        result = apply_benjamini_hochberg(p_values)
        
        expected = [0.04, 0.05333333333333333, 0.05333333333333333, 0.20]
        
        assert len(result) == len(expected)
        for r, e in zip(result, expected):
            assert np.isclose(r, e), f"Expected {e}, got {r}"

    def test_bh_correction_capping_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.8, 0.9, 0.95]
        result = apply_benjamini_hochberg(p_values)
        
        for r in result:
            assert r <= 1.0, f"Adjusted p-value {r} exceeds 1.0"

    def test_bh_correction_with_numpy_array(self):
        """Test that the function accepts numpy arrays as input."""
        p_values = np.array([0.01, 0.05, 0.10])
        result = apply_benjamini_hochberg(p_values)
        assert len(result) == 3
        assert isinstance(result, list) or isinstance(result, np.ndarray)

    def test_bh_correction_preserves_significance_threshold(self):
        """
        Verify that if all original p-values are below alpha, 
        the adjusted values reflect the FDR control appropriately.
        """
        # All p-values are very small
        p_values = [0.001, 0.002, 0.003]
        result = apply_benjamini_hochberg(p_values)
        
        # They should still be relatively small, though increased
        for r in result:
            assert r < 0.1, f"Adjusted p-value {r} is unexpectedly large for very small inputs"

    def test_bh_correction_integration_with_correlation_module(self):
        """
        Integration test: Verify apply_benjamini_hochberg works correctly
        when called in the context of the correlation module's expected usage.
        """
        # Simulate a list of p-values that might come from multiple correlation tests
        simulated_p_values = [0.005, 0.02, 0.08, 0.15, 0.03, 0.40, 0.01]
        
        adjusted = apply_benjamini_hochberg(simulated_p_values)
        
        # Verify the logic:
        # 1. Length matches
        assert len(adjusted) == len(simulated_p_values)
        
        # 2. Monotonicity check (as done in test_bh_correction_monotonicity)
        paired = list(zip(simulated_p_values, adjusted))
        paired.sort(key=lambda x: x[0])
        adjusted_sorted = [x[1] for x in paired]
        for i in range(len(adjusted_sorted) - 1):
            assert adjusted_sorted[i] <= adjusted_sorted[i+1]
        
        # 3. Values are within [0, 1]
        for val in adjusted:
            assert 0 <= val <= 1.0