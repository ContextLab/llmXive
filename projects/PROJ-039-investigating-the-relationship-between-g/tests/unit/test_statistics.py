"""
Unit tests for statistical correction methods, specifically the Benjamini-Hochberg FDR correction.

This module verifies the logic of the FDR correction as used in the 
gut-microbiome-eeg-alpha analysis pipeline.
"""
import pytest
import numpy as np
from typing import List, Tuple
import sys
import os

# Add the code directory to the path to allow imports if running as a script
# In a standard pytest run, the path should be configured via conftest or PYTHONPATH
code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from utils import fdr_benjamini_hochberg


class TestBenjaminiHochberg:
    """Test suite for the Benjamini-Hochberg FDR correction implementation."""

    def test_constant_pvalues(self):
        """Test with constant p-values (all significant or all not depending on q)."""
        # If all p-values are 0.05 and q=0.1, with n=10:
        # Sorted: 0.05, 0.05, ...
        # Thresholds: 0.1 * (i+1)/10
        # i=0: 0.01 < 0.05 (False)
        # ...
        # i=9: 0.1 * 10/10 = 0.1 >= 0.05 (True) -> All should be significant if the logic holds for the max
        # Actually, BH finds the largest k such that p(k) <= (k/m)*q.
        # Here, p(k) = 0.05 for all k.
        # k=1: 0.05 <= 0.1 * 1/10 = 0.01 (False)
        # k=10: 0.05 <= 0.1 * 10/10 = 0.1 (True)
        # So k=10 is the largest. All 10 should be significant.
        
        p_values = [0.05] * 10
        q = 0.1
        significant = fdr_benjamini_hochberg(p_values, q)
        
        # All should be significant
        assert all(significant), "All p-values should be significant at q=0.1"
        assert len(significant) == 10

    def test_mixed_pvalues(self):
        """Test with a mix of significant and non-significant p-values."""
        p_values = [0.001, 0.01, 0.02, 0.04, 0.05, 0.06, 0.08, 0.12, 0.20, 0.50]
        q = 0.1
        
        # Manual calculation for verification:
        # m = 10
        # Sorted p: same as input
        # Thresholds (k/m * q):
        # 1: 0.01 -> 0.001 <= 0.01 (True)
        # 2: 0.02 -> 0.01 <= 0.02 (True)
        # 3: 0.03 -> 0.02 <= 0.03 (True)
        # 4: 0.04 -> 0.04 <= 0.04 (True)
        # 5: 0.05 -> 0.05 <= 0.05 (True)
        # 6: 0.06 -> 0.06 <= 0.06 (True)
        # 7: 0.07 -> 0.08 <= 0.07 (False) -> Stop here.
        # Largest k is 6.
        # All p-values <= p(6) are significant.
        # p(6) is 0.06.
        # So indices 0 to 5 should be significant.
        
        significant = fdr_benjamini_hochberg(p_values, q)
        
        expected = [True, True, True, True, True, True, False, False, False, False]
        assert significant == expected, f"Expected {expected}, got {significant}"

    def test_very_small_q(self):
        """Test with a very small q value where nothing should be significant."""
        p_values = [0.01, 0.02, 0.03]
        q = 0.001
        
        significant = fdr_benjamini_hochberg(p_values, q)
        
        # Thresholds:
        # 1: 0.001 * 1/3 = 0.00033 < 0.01
        # 2: 0.001 * 2/3 = 0.00066 < 0.02
        # 3: 0.001 * 3/3 = 0.001 < 0.03
        # No k satisfies condition.
        expected = [False, False, False]
        assert significant == expected

    def test_very_large_q(self):
        """Test with a very large q value where everything should be significant."""
        p_values = [0.01, 0.02, 0.03]
        q = 1.0
        
        significant = fdr_benjamini_hochberg(p_values, q)
        
        # Thresholds:
        # 1: 1.0 * 1/3 = 0.33 >= 0.01
        # All should be significant.
        expected = [True, True, True]
        assert significant == expected

    def test_single_pvalue_significant(self):
        """Test with a single p-value that is significant."""
        p_values = [0.05]
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == [True]

    def test_single_pvalue_not_significant(self):
        """Test with a single p-value that is not significant."""
        p_values = [0.2]
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == [False]

    def test_unsorted_input(self):
        """Test that the function handles unsorted input correctly."""
        # Input is not sorted
        p_values = [0.05, 0.001, 0.02]
        q = 0.1
        
        # Sorted: 0.001, 0.02, 0.05
        # m = 3
        # 1: 0.1 * 1/3 = 0.033 >= 0.001 (True)
        # 2: 0.1 * 2/3 = 0.066 >= 0.02 (True)
        # 3: 0.1 * 3/3 = 0.1 >= 0.05 (True)
        # All significant.
        
        significant = fdr_benjamini_hochberg(p_values, q)
        
        # The function should return significance in the ORIGINAL order
        # All are significant, so all True.
        expected = [True, True, True]
        assert significant == expected

    def test_unsorted_input_mixed(self):
        """Test unsorted input where some are significant and some are not."""
        # Values: 0.08 (idx 0), 0.001 (idx 1), 0.06 (idx 2)
        # Sorted: 0.001, 0.06, 0.08
        # m = 3, q = 0.1
        # 1: 0.033 >= 0.001 (True)
        # 2: 0.066 >= 0.06 (True)
        # 3: 0.1 >= 0.08 (True)
        # All significant?
        # Wait, 0.08 <= 0.1 is True.
        # Let's pick values that fail.
        # 0.09, 0.001, 0.08.
        # Sorted: 0.001, 0.08, 0.09
        # 1: 0.033 >= 0.001 (True)
        # 2: 0.066 >= 0.08 (False) -> Stop. k=1.
        # Only the smallest is significant.
        
        p_values = [0.09, 0.001, 0.08] # Original order: 0.09, 0.001, 0.08
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        
        # Sorted: 0.001 (orig idx 1), 0.08 (orig idx 2), 0.09 (orig idx 0)
        # k=1 (val 0.001) is significant.
        # k=2 (val 0.08) is NOT significant (0.08 > 0.066).
        # So only orig idx 1 should be True.
        expected = [False, True, False]
        assert significant == expected, f"Expected {expected}, got {significant}"

    def test_empty_list(self):
        """Test behavior with an empty list of p-values."""
        p_values = []
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == []

    def test_duplicate_pvalues(self):
        """Test with duplicate p-values."""
        p_values = [0.01, 0.01, 0.01]
        q = 0.1
        
        # Sorted: 0.01, 0.01, 0.01
        # 1: 0.033 >= 0.01 (True)
        # 2: 0.066 >= 0.01 (True)
        # 3: 0.1 >= 0.01 (True)
        # All significant.
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == [True, True, True]

    def test_pvalues_exactly_on_threshold(self):
        """Test p-values exactly equal to the threshold."""
        # m=2, q=0.1
        # Thresholds: 0.05, 0.1
        # p = [0.05, 0.1]
        # 1: 0.05 <= 0.05 (True)
        # 2: 0.1 <= 0.1 (True)
        p_values = [0.05, 0.1]
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == [True, True]

    def test_pvalues_just_above_threshold(self):
        """Test p-values just above the threshold."""
        # m=2, q=0.1
        # Thresholds: 0.05, 0.1
        # p = [0.051, 0.101]
        # 1: 0.051 <= 0.05 (False)
        # 2: 0.101 <= 0.1 (False)
        p_values = [0.051, 0.101]
        q = 0.1
        
        significant = fdr_benjamini_hochberg(p_values, q)
        assert significant == [False, False]