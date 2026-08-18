"""
Unit tests for FDR correction and one-sample t-test logic in glm_group.py.

This module tests the statistical core of the group-level analysis:
1. One-sample t-test against zero (verifying t-statistic and p-value calculation).
2. Benjamini-Hochberg FDR correction (verifying q-values and thresholding).

Dependencies:
- numpy
- scipy.stats
- statsmodels.stats.multitest (for independent verification)
"""
import numpy as np
import pytest
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Import the functions we intend to test.
# We assume these will be implemented in code/glm_group.py.
# If they don't exist yet, this file serves as the TDD definition for them.
try:
    from code.glm_group import one_sample_ttest, apply_fdr_correction
except ImportError:
    # Fallback for testing environment where implementation might not exist yet.
    # In a real TDD flow, we would define these here temporarily to test the test,
    # but per constraints, we write the test assuming the implementation exists.
    # If the implementation is missing, the test runner will catch ImportError.
    raise ImportError(
        "Implementation file code/glm_group.py not found or missing required functions. "
        "This test expects 'one_sample_ttest' and 'apply_fdr_correction' to be defined there."
    )


class TestOneSampleTTest:
    """Tests for the one-sample t-test logic."""

    def test_t_statistic_calculation(self):
        """Verify t-statistic is calculated correctly against zero."""
        # Generate a known dataset: mean=10, std=2, n=20
        # Expected t = (mean - 0) / (std / sqrt(n))
        np.random.seed(42)
        data = np.random.normal(loc=10, scale=2, size=20)
        
        t_stat, p_val = one_sample_ttest(data)

        # Manual calculation for verification
        expected_t = np.mean(data) / (np.std(data, ddof=1) / np.sqrt(len(data)))
        
        # Assert t-statistic matches (allow small float tolerance)
        assert np.isclose(t_stat, expected_t), f"Expected t={expected_t}, got {t_stat}"

    def test_p_value_calculation(self):
        """Verify p-value matches scipy.stats implementation."""
        np.random.seed(123)
        data = np.random.normal(loc=5, scale=3, size=50)
        
        t_stat, p_val = one_sample_ttest(data)
        
        # Compare with scipy
        scipy_t, scipy_p = stats.ttest_1samp(data, popmean=0.0, alternative='two-sided')
        
        assert np.isclose(t_stat, scipy_t), "T-statistic mismatch with scipy"
        assert np.isclose(p_val, scipy_p), "P-value mismatch with scipy"

    def test_empty_input_raises(self):
        """Ensure empty input raises an error."""
        with pytest.raises(ValueError):
            one_sample_ttest(np.array([]))

    def test_single_value(self):
        """Test behavior with a single value (undefined std, should raise or handle)."""
        # t-test with n=1 is mathematically undefined (division by zero in std error)
        # SciPy raises a warning or returns nan. We expect our wrapper to handle or raise.
        data = np.array([5.0])
        # We expect this to either raise or return nan. Let's check scipy behavior first.
        # scipy.ttest_1samp raises a warning for n=1.
        # We will assert that our function handles it gracefully (raises ValueError)
        # to prevent downstream crashes, consistent with "fail loudly" principle.
        with pytest.raises(ValueError):
            one_sample_ttest(data)


class TestApplyFDRCorrection:
    """Tests for the Benjamini-Hochberg FDR correction logic."""

    def test_fdr_thresholding(self):
        """Verify that FDR correction correctly thresholds p-values."""
        # Create a set of p-values where we know the outcome
        # q < 0.05
        p_values = np.array([0.001, 0.02, 0.04, 0.06, 0.10, 0.50])
        alpha = 0.05
        
        significant_indices = apply_fdr_correction(p_values, alpha)
        
        # Expected: 0.001, 0.02, 0.04 should be significant (indices 0, 1, 2)
        # 0.06 is likely not significant in BH procedure for this small set
        # Let's verify against statsmodels
        reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        expected_indices = np.where(reject)[0]
        
        assert set(significant_indices) == set(expected_indices), \
            f"Expected indices {expected_indices}, got {significant_indices}"

    def test_all_significant(self):
        """Test case where all p-values are extremely small."""
        p_values = np.array([1e-5, 1e-6, 1e-7])
        alpha = 0.05
        
        significant_indices = apply_fdr_correction(p_values, alpha)
        expected_indices = [0, 1, 2]
        
        assert set(significant_indices) == set(expected_indices)

    def test_none_significant(self):
        """Test case where no p-values survive correction."""
        p_values = np.array([0.2, 0.5, 0.8])
        alpha = 0.05
        
        significant_indices = apply_fdr_correction(p_values, alpha)
        
        assert len(significant_indices) == 0

    def test_alpha_edge_case(self):
        """Test with alpha=1.0 (all should pass if p < 1)."""
        p_values = np.array([0.5, 0.9, 0.99])
        alpha = 1.0
        
        significant_indices = apply_fdr_correction(p_values, alpha)
        # With alpha=1.0, BH should accept everything < 1.0
        assert set(significant_indices) == {0, 1, 2}

    def test_invalid_input(self):
        """Test with non-array input."""
        with pytest.raises((ValueError, TypeError)):
            apply_fdr_correction([0.1, 0.2], 0.05) # Should handle list or raise

    def test_q_value_calculation(self):
        """Verify that the function correctly calculates q-values (optional return)."""
        # This test ensures the logic matches the BH algorithm step-by-step
        # p = [0.001, 0.02, 0.04, 0.06, 0.10, 0.50]
        # n = 6
        # Rank 1: 0.001 * 6 / 1 = 0.006
        # Rank 2: 0.02 * 6 / 2 = 0.06
        # Rank 3: 0.04 * 6 / 3 = 0.08
        # Rank 4: 0.06 * 6 / 4 = 0.09
        # Rank 5: 0.10 * 6 / 5 = 0.12
        # Rank 6: 0.50 * 6 / 6 = 0.50
        # Cumulative min from bottom:
        # 6: 0.50
        # 5: min(0.12, 0.50) = 0.12
        # 4: min(0.09, 0.12) = 0.09
        # 3: min(0.08, 0.09) = 0.08
        # 2: min(0.06, 0.08) = 0.06
        # 1: min(0.006, 0.06) = 0.006
        # Threshold 0.05: Only rank 1 (0.001) is < 0.05? 
        # Wait, BH condition: p(i) <= (i/n) * alpha
        # 0.001 <= (1/6)*0.05 = 0.0083 -> Yes
        # 0.02 <= (2/6)*0.05 = 0.016 -> No (0.02 > 0.016)
        # So only index 0 should be significant.
        
        p_values = np.array([0.001, 0.02, 0.04, 0.06, 0.10, 0.50])
        significant_indices = apply_fdr_correction(p_values, 0.05)
        assert significant_indices == [0], f"Expected [0], got {significant_indices}"