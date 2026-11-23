"""
Unit tests for statistical correction methods in analysis.stats.
Specifically tests FDR correction (Benjamini-Hochberg) as per T021.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats

# Import the function under test from the project's stats module
from analysis.stats import fdr_correction_benjamini_hochberg


class TestFDRCorrection:
    """Tests for the Benjamini-Hochberg FDR correction implementation."""

    def test_fdr_correction_known_values(self):
        """
        Implement test_fdr_correction with known p-values and expected q-values.
        
        Uses a standard example to verify the Benjamini-Hochberg procedure.
        Input p-values: [0.01, 0.03, 0.04, 0.08, 0.12]
        Sorted indices: 0, 1, 2, 3, 4
        n = 5
        
        Expected calculation steps:
        1. Sort p-values: [0.01, 0.03, 0.04, 0.08, 0.12] (already sorted)
        2. Calculate rank (i+1) for each: [1, 2, 3, 4, 5]
        3. Calculate BH critical value: (i+1)/n * alpha (we don't use alpha here, we calculate q)
        4. Calculate q-values: p * n / (i+1)
           - 0.01 * 5 / 1 = 0.05
           - 0.03 * 5 / 2 = 0.075
           - 0.04 * 5 / 3 = 0.0666...
           - 0.08 * 5 / 4 = 0.10
           - 0.12 * 5 / 5 = 0.12
        5. Enforce monotonicity (cumulative min from right to left):
           - q[4] = 0.12
           - q[3] = min(0.10, 0.12) = 0.10
           - q[2] = min(0.0666, 0.10) = 0.0666
           - q[1] = min(0.075, 0.0666) = 0.0666
           - q[0] = min(0.05, 0.0666) = 0.05
        
        Expected q-values (approx): [0.05, 0.066667, 0.066667, 0.10, 0.12]
        """
        p_values = np.array([0.01, 0.03, 0.04, 0.08, 0.12])
        expected_q_values = np.array([0.05, 0.06666667, 0.06666667, 0.10, 0.12])
        
        q_values = fdr_correction_benjamini_hochberg(p_values)
        
        assert q_values is not None, "FDR correction returned None"
        assert len(q_values) == len(p_values), "Output length does not match input length"
        
        # Check values with tolerance for floating point arithmetic
        np.testing.assert_array_almost_equal(q_values, expected_q_values, decimal=6)

    def test_fdr_correction_unsorted_input(self):
        """
        Test that the function correctly handles unsorted p-values.
        The BH procedure requires sorting first.
        """
        p_values = np.array([0.08, 0.01, 0.12, 0.03, 0.04])
        # Expected result should be the same as the sorted case, just mapped back to original order
        # Sorted: [0.01, 0.03, 0.04, 0.08, 0.12] -> q: [0.05, 0.0666, 0.0666, 0.10, 0.12]
        # Original order indices: 1, 3, 4, 0, 2
        # Expected q in original order: [0.10, 0.05, 0.12, 0.0666, 0.0666]
        expected_q_values = np.array([0.10, 0.05, 0.12, 0.06666667, 0.06666667])
        
        q_values = fdr_correction_benjamini_hochberg(p_values)
        
        np.testing.assert_array_almost_equal(q_values, expected_q_values, decimal=6)

    def test_fdr_correction_pandas_series(self):
        """Test that the function accepts pandas Series as input."""
        p_values = pd.Series([0.01, 0.03, 0.04])
        
        q_values = fdr_correction_benjamini_hochberg(p_values)
        
        assert q_values is not None
        assert len(q_values) == 3
        # Verify monotonicity
        assert np.all(np.diff(q_values) >= 0) or len(q_values) == 1

    def test_fdr_correction_edge_cases(self):
        """Test edge cases like all p=0, all p=1, single value."""
        # Single value
        p_single = np.array([0.05])
        q_single = fdr_correction_benjamini_hochberg(p_single)
        assert q_single[0] == 0.05  # p * 1 / 1 = p
        
        # All ones (should remain ones)
        p_ones = np.array([1.0, 1.0, 1.0])
        q_ones = fdr_correction_benjamini_hochberg(p_ones)
        np.testing.assert_array_almost_equal(q_ones, p_ones)
        
        # All zeros (should remain zeros)
        p_zeros = np.array([0.0, 0.0, 0.0])
        q_zeros = fdr_correction_benjamini_hochberg(p_zeros)
        np.testing.assert_array_almost_equal(q_zeros, p_zeros)

    def test_fdr_correction_monotonicity_enforcement(self):
        """
        Test that the cumulative minimum step enforces monotonicity correctly.
        This is the critical step that distinguishes BH from simple p*n/i.
        """
        # Construct a case where simple p*n/i would violate monotonicity
        # p = [0.05, 0.06, 0.07]
        # n=3
        # raw_q = [0.05*3/1=0.15, 0.06*3/2=0.09, 0.07*3/3=0.07]
        # This is decreasing: 0.15 > 0.09 > 0.07, which is invalid for sorted p.
        # Wait, p is sorted, so q must be non-decreasing.
        # Actually, the raw calculation p_i * n / i can decrease if p_i increases slowly.
        # Example: p=[0.1, 0.11, 0.12], n=3
        # q_raw = [0.3, 0.165, 0.12] -> Decreasing!
        # BH requires q[i] <= q[i+1]. So we take cummin from the right.
        # q_corrected = [0.12, 0.12, 0.12]
        
        p_values = np.array([0.10, 0.11, 0.12])
        q_values = fdr_correction_benjamini_hochberg(p_values)
        
        # Check monotonicity
        assert np.all(np.diff(q_values) >= -1e-9), "Q-values must be monotonically non-decreasing"
        
        # In this specific case, all q-values should be capped by the smallest valid q (the last one)
        # because the raw calculation drops.
        # Last raw: 0.12 * 3 / 3 = 0.12
        # Middle raw: 0.11 * 3 / 2 = 0.165 -> capped to 0.12
        # First raw: 0.10 * 3 / 1 = 0.30 -> capped to 0.12
        expected = np.array([0.12, 0.12, 0.12])
        np.testing.assert_array_almost_equal(q_values, expected, decimal=6)

    def test_fdr_correction_comparison_with_scipy(self):
        """
        Compare our implementation with scipy.stats.multipletests (if available)
        to ensure correctness.
        """
        try:
            from statsmodels.stats.multitest import multipletests
        except ImportError:
            pytest.skip("statsmodels not available for comparison")

        p_values = np.array([0.001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.9])
        
        # Our implementation
        q_ours = fdr_correction_benjamini_hochberg(p_values)
        
        # Scipy/Statsmodels implementation (method='fdr_bh')
        _, q_theirs, _, _ = multipletests(p_values, method='fdr_bh')
        
        np.testing.assert_array_almost_equal(q_ours, q_theirs, decimal=6)

    def test_fdr_correction_output_type(self):
        """Ensure the function returns a numpy array."""
        p_values = [0.01, 0.05, 0.1]
        q_values = fdr_correction_benjamini_hochberg(p_values)
        
        assert isinstance(q_values, np.ndarray), "Output should be a numpy array"
        assert q_values.dtype in [np.float32, np.float64], "Output should be float"