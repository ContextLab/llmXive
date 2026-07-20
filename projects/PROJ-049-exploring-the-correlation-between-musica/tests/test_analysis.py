import pytest
import numpy as np
import pandas as pd
from code.analysis import apply_fdr_correction

class TestBenjaminiHochbergFDR:
    """
    Unit tests for the Benjamini-Hochberg FDR correction logic in code/analysis.py.
    
    These tests verify that the p-value adjustment logic correctly implements
    the Benjamini-Hochberg procedure for controlling the False Discovery Rate.
    """

    def test_fdr_correction_simple_monotonic(self):
        """
        Test FDR correction with a simple, known monotonic set of p-values.
        
        Input: [0.001, 0.01, 0.02, 0.05, 0.10]
        m = 5 tests.
        
        Expected calculation (BH procedure):
        1. Sort p-values: [0.001, 0.01, 0.02, 0.05, 0.10] (already sorted)
        2. Calculate critical values: (i/m) * alpha for alpha=0.05
           i=1: 0.01 * 0.05 = 0.0005
           i=2: 0.02 * 0.05 = 0.0010
           i=3: 0.03 * 0.05 = 0.0015
           i=4: 0.04 * 0.05 = 0.0020
           i=5: 0.05 * 0.05 = 0.0025
        3. Find largest k where p_k <= (k/m)*alpha.
           Here, none of the p-values are <= their critical values?
           Wait, standard BH adjusted p-value formula is:
           p_adj[i] = min(1, min_{j>=i} (m/j * p[j]))
        
        Let's re-verify the logic against the standard definition:
        Adjusted p-value for rank i (1-based) = (m/i) * p[i]
        Then enforce monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1])
        
        Input: [0.001, 0.01, 0.02, 0.05, 0.10], m=5
        Raw adj:
          1: 5/1 * 0.001 = 0.005
          2: 5/2 * 0.010 = 0.025
          3: 5/3 * 0.020 = 0.0333...
          4: 5/4 * 0.050 = 0.0625
          5: 5/5 * 0.100 = 0.100
        
        Monotonicity enforcement (cumulative min from right):
          5: 0.100
          4: min(0.0625, 0.100) = 0.0625
          3: min(0.0333, 0.0625) = 0.0333
          2: min(0.025, 0.0333) = 0.025
          1: min(0.005, 0.025) = 0.005
        
        Expected output (sorted back to original order): [0.005, 0.025, 0.0333, 0.0625, 0.100]
        """
        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.10])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        expected = np.array([0.005, 0.025, 1/30, 0.0625, 0.100])
        # 1/30 is approx 0.03333333333333333
        
        np.testing.assert_almost_equal(result, expected, decimal=6)
        
        # Verify significance flags
        # 0.005 < 0.05 -> True
        # 0.025 < 0.05 -> True
        # 0.0333 < 0.05 -> True
        # 0.0625 > 0.05 -> False
        # 0.100 > 0.05 -> False
        expected_significant = np.array([True, True, True, False, False])
        assert np.array_equal(result['is_significant'], expected_significant)

    def test_fdr_correction_unsorted_input(self):
        """
        Test that FDR correction handles unsorted input correctly.
        
        Input: [0.10, 0.001, 0.05, 0.02, 0.01]
        Sorted: [0.001, 0.01, 0.02, 0.05, 0.10]
        m = 5
        
        Expected adjusted values (based on sorted ranks):
        Rank 1 (0.001): 0.005
        Rank 2 (0.01): 0.025
        Rank 3 (0.02): 0.0333
        Rank 4 (0.05): 0.0625
        Rank 5 (0.10): 0.100
        
        Mapped back to original order:
        0.10 -> 0.100
        0.001 -> 0.005
        0.05 -> 0.0625
        0.02 -> 0.0333
        0.01 -> 0.025
        """
        p_values = np.array([0.10, 0.001, 0.05, 0.02, 0.01])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        expected_values = np.array([0.100, 0.005, 0.0625, 1/30, 0.025])
        
        np.testing.assert_almost_equal(result['adjusted_p_value'], expected_values, decimal=6)

    def test_fdr_correction_with_ties(self):
        """
        Test FDR correction with duplicate p-values.
        
        Input: [0.01, 0.01, 0.01, 0.05]
        m = 4
        
        Sorted: [0.01, 0.01, 0.01, 0.05]
        Ranks: 1, 2, 3, 4
        
        Raw adj:
          1: 4/1 * 0.01 = 0.04
          2: 4/2 * 0.01 = 0.02
          3: 4/3 * 0.01 = 0.0133
          4: 4/4 * 0.05 = 0.05
        
        Monotonicity (min from right):
          4: 0.05
          3: min(0.0133, 0.05) = 0.0133
          2: min(0.02, 0.0133) = 0.0133
          1: min(0.04, 0.0133) = 0.0133
        
        Expected: [0.0133, 0.0133, 0.0133, 0.05]
        """
        p_values = np.array([0.01, 0.01, 0.01, 0.05])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        expected = np.array([1/75, 1/75, 1/75, 0.05]) # 1/75 = 0.01333...
        
        np.testing.assert_almost_equal(result['adjusted_p_value'], expected, decimal=6)

    def test_fdr_correction_all_significant(self):
        """
        Test case where all p-values are significant after correction.
        """
        p_values = np.array([0.0001, 0.0002, 0.0003])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        # All should be < 0.05
        assert all(result['is_significant'])

    def test_fdr_correction_none_significant(self):
        """
        Test case where no p-values are significant after correction.
        """
        p_values = np.array([0.5, 0.6, 0.7])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        # None should be < 0.05
        assert not any(result['is_significant'])

    def test_fdr_correction_single_value(self):
        """
        Test FDR correction with a single p-value.
        BH reduces to standard p-value check.
        """
        p_values = np.array([0.04])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        assert result['adjusted_p_value'][0] == 0.04
        assert result['is_significant'][0] == True

    def test_fdr_correction_boundary(self):
        """
        Test FDR correction where a p-value is exactly at the boundary.
        """
        # m=2, alpha=0.05
        # p = [0.025, 0.05]
        # Rank 1 (0.025): 2/1 * 0.025 = 0.05
        # Rank 2 (0.05): 2/2 * 0.05 = 0.05
        # Both should be significant if <= 0.05
        p_values = np.array([0.025, 0.05])
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        # Both adjusted p-values should be 0.05
        assert result['adjusted_p_value'][0] == 0.05
        assert result['adjusted_p_value'][1] == 0.05
        
        # Both should be significant (<= alpha)
        assert all(result['is_significant'])

    def test_fdr_correction_large_dataset(self):
        """
        Test FDR correction with a larger, random dataset to ensure performance and correctness.
        """
        np.random.seed(42)
        n = 1000
        p_values = np.random.uniform(0, 1, n)
        alpha = 0.05
        
        result = apply_fdr_correction(p_values, alpha)
        
        # Verify output shape
        assert len(result['adjusted_p_value']) == n
        assert len(result['is_significant']) == n
        
        # Verify monotonicity of adjusted p-values when sorted by original p-value
        sort_idx = np.argsort(p_values)
        adj_sorted = result['adjusted_p_value'][sort_idx]
        assert np.all(np.diff(adj_sorted) >= -1e-9) # Allow small floating point errors
        
        # Verify all adjusted p-values are <= 1.0
        assert np.all(result['adjusted_p_value'] <= 1.0)
        
        # Verify all adjusted p-values are >= 0.0
        assert np.all(result['adjusted_p_value'] >= 0.0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])