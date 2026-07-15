import pandas as pd
import numpy as np
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_benjamini_hochberg

class TestBenjaminiHochberg:
    def test_bh_basic_significance(self):
        """Test that BH correctly identifies significant p-values in a simple case."""
        # Create a set of p-values where we know the outcome
        # Sorted: 0.001, 0.01, 0.02, 0.1, ...
        # n=10, alpha=0.05
        # Thresholds: (i/10)*0.05 -> 0.005, 0.01, 0.015, 0.02, ...
        # 0.001 <= 0.005 (True)
        # 0.01 <= 0.01 (True)
        # 0.02 <= 0.015 (False) -> k=2
        p_values = pd.Series([0.001, 0.01, 0.02, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        # Expected: 0.001, 0.01 should be significant (k=2)
        assert result['significant'].sum() == 2
        assert result['significant'].iloc[0] == True
        assert result['significant'].iloc[1] == True
        assert result['significant'].iloc[2] == False

    def test_bh_all_significant(self):
        """Test case where all p-values are very small."""
        p_values = pd.Series([0.0001, 0.0002, 0.0003, 0.0004, 0.0005])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        # All should be significant
        assert result['significant'].sum() == 5
        assert all(result['significant'])

    def test_bh_none_significant(self):
        """Test case where no p-values are significant."""
        p_values = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        # None should be significant
        assert result['significant'].sum() == 0
        assert not any(result['significant'])

    def test_bh_adjusted_p_values_monotonic(self):
        """Test that adjusted p-values are monotonic with respect to raw p-values."""
        p_values = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        adj_p = result['adjusted_p_values']
        # Adjusted p-values should be non-decreasing
        for i in range(len(adj_p) - 1):
            assert adj_p.iloc[i] <= adj_p.iloc[i+1], f"Monotonicity violated at index {i}"

    def test_bh_adjusted_p_values_capped_at_1(self):
        """Test that adjusted p-values do not exceed 1.0."""
        p_values = pd.Series([0.9, 0.95, 0.99, 1.0])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        assert all(result['adjusted_p_values'] <= 1.0)

    def test_bh_empty_input(self):
        """Test handling of empty p-value series."""
        p_values = pd.Series([], dtype=float)
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        assert len(result['significant']) == 0
        assert len(result['adjusted_p_values']) == 0
        assert result['threshold'] == 0.0

    def test_bh_single_value(self):
        """Test handling of a single p-value."""
        p_values = pd.Series([0.03])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        # For n=1, threshold is 1/1 * 0.05 = 0.05. 0.03 <= 0.05 -> Significant
        assert result['significant'].iloc[0] == True
        assert result['adjusted_p_values'].iloc[0] <= 1.0

    def test_bh_preserves_original_order(self):
        """Test that the function returns results in the original input order."""
        # Input is unsorted
        p_values = pd.Series([0.05, 0.01, 0.02, 0.03])
        result = run_benjamini_hochberg(p_values, alpha=0.05)
        
        # The result should align with the input order
        # Input index 0: 0.05 -> Should be significant? (4/4 * 0.05 = 0.05, yes)
        # Input index 1: 0.01 -> Significant
        # Input index 2: 0.02 -> Significant
        # Input index 3: 0.03 -> Significant
        # Wait, let's re-verify logic.
        # Sorted: 0.01, 0.02, 0.03, 0.05. n=4.
        # i=1 (0.01) <= 0.0125 (True)
        # i=2 (0.02) <= 0.025 (True)
        # i=3 (0.03) <= 0.0375 (True)
        # i=4 (0.05) <= 0.05 (True)
        # All significant.
        
        assert len(result) == 4
        assert all(result['significant'])
        # Ensure the index matches the input
        assert list(result.index) == list(p_values.index)