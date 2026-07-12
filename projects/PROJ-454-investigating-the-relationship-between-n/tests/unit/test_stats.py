"""
Unit tests for FDR correction logic in utils.stats_utils.
Specifically tests the Benjamini-Hochberg procedure implementation.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch
from utils.stats_utils import fdr_benjamini_hochberg


class TestFDRBenjaminiHochberg:
    """Test suite for the Benjamini-Hochberg FDR correction function."""

    def test_fdr_basic_rejection(self):
        """Test that FDR correctly identifies significant results with a known input."""
        # Known p-values where some are clearly significant
        p_values = np.array([0.001, 0.01, 0.03, 0.04, 0.10, 0.50, 0.80])
        alpha = 0.05
        n = len(p_values)

        # Sort p-values (BH requires sorted input, but function should handle it)
        sorted_p = np.sort(p_values)
        
        # Calculate BH critical values: (i/n) * alpha
        # i ranges from 1 to n
        critical_values = (np.arange(1, n + 1) / n) * alpha
        
        # Find the largest k such that p_k <= critical_k
        # Then all p_1...p_k are significant
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)

        # Manual verification of expected results for this specific set
        # i=1: 0.001 <= (1/7)*0.05 = 0.0071 -> True
        # i=2: 0.010 <= (2/7)*0.05 = 0.0143 -> True
        # i=3: 0.030 <= (3/7)*0.05 = 0.0214 -> False (0.03 > 0.0214)
        # Wait, let's re-calculate carefully.
        # Sorted p: [0.001, 0.01, 0.03, 0.04, 0.10, 0.50, 0.80]
        # Critical: [0.0071, 0.0143, 0.0214, 0.0286, 0.0357, 0.0429, 0.0500]
        
        # Comparison:
        # 0.001 <= 0.0071 (True)
        # 0.010 <= 0.0143 (True)
        # 0.030 <= 0.0214 (False)
        # 0.040 <= 0.0286 (False)
        # ...
        # The largest k where p_k <= crit_k is k=2.
        # So indices corresponding to 0.001 and 0.01 should be True.
        
        expected_significant_count = 2
        assert np.sum(significant_mask) == expected_significant_count, \
            f"Expected {expected_significant_count} significant, got {np.sum(significant_mask)}"

    def test_fdr_all_significant(self):
        """Test case where all p-values are very small."""
        p_values = np.array([0.0001, 0.0002, 0.0003, 0.0004])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        assert np.all(significant_mask), "All p-values should be significant"

    def test_fdr_none_significant(self):
        """Test case where no p-values are significant."""
        p_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        assert not np.any(significant_mask), "No p-values should be significant"

    def test_fdr_with_dataframe(self):
        """Test FDR correction on a pandas Series."""
        p_values = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        # Should return a boolean array/Series of same length
        assert len(significant_mask) == len(p_values)
        assert isinstance(significant_mask, (np.ndarray, pd.Series))

    def test_fdr_alpha_sensitivity(self):
        """Test that changing alpha changes the number of rejections."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
        
        mask_strict = fdr_benjamini_hochberg(p_values, alpha=0.01)
        mask_lenient = fdr_benjamini_hochberg(p_values, alpha=0.10)
        
        assert np.sum(mask_strict) <= np.sum(mask_lenient), \
            "Strict alpha should result in fewer or equal rejections"

    def test_fdr_edge_case_single_value(self):
        """Test FDR with a single p-value."""
        p_values = np.array([0.01])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        assert len(significant_mask) == 1
        assert significant_mask[0] == True, "Single p-value < alpha should be significant"

    def test_fdr_edge_case_single_value_non_sig(self):
        """Test FDR with a single non-significant p-value."""
        p_values = np.array([0.10])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        assert significant_mask[0] == False, "Single p-value > alpha should not be significant"

    def test_fdr_unsorted_input(self):
        """Test that FDR handles unsorted input correctly."""
        # Intentionally unsorted
        p_values = np.array([0.04, 0.01, 0.03, 0.02, 0.05])
        alpha = 0.05
        
        # The function should sort internally or handle it
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        # Check that the output has the correct length
        assert len(significant_mask) == len(p_values)
        # The logic should still hold: smallest values get rejected
        # With alpha=0.05 and n=5:
        # Sorted: 0.01, 0.02, 0.03, 0.04, 0.05
        # Crit:   0.01, 0.02, 0.03, 0.04, 0.05
        # All should be significant (p <= crit)
        assert np.sum(significant_mask) == 5, "All values should be significant in this edge case"

    def test_fdr_with_ties(self):
        """Test FDR with tied p-values."""
        p_values = np.array([0.01, 0.01, 0.01, 0.05, 0.05])
        alpha = 0.05
        
        significant_mask = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        # All 0.01s should be significant. 
        # For 0.05s: 
        # Sorted: 0.01, 0.01, 0.01, 0.05, 0.05
        # Crit:   0.01, 0.02, 0.03, 0.04, 0.05
        # 0.05 <= 0.05 is True. So all should be significant.
        assert np.sum(significant_mask) == 5

    def test_fdr_returns_boolean_array(self):
        """Ensure the return type is a boolean array."""
        p_values = np.array([0.01, 0.5, 0.9])
        alpha = 0.05
        
        result = fdr_benjamini_hochberg(p_values, alpha=alpha)
        
        assert result.dtype == bool, "Result must be a boolean array"