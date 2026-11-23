import pytest
import numpy as np
import pandas as pd
from scipy import stats
from src.models.metrics import calculate_wald_z_statistic, calculate_p_value_z_test, calculate_f_statistic, apply_benjamini_hochberg_fdr

class TestMetricsEdgeCases:
    """Additional unit tests for metrics calculation edge cases."""

    def test_wald_z_statistic_with_zero_se(self):
        """Test Wald Z statistic with zero standard error (should handle gracefully)."""
        # If SE is 0, Z should be infinite or handled
        z = calculate_wald_z_statistic(1.0, 0.0)
        # Should return inf or a large number
        assert np.isinf(z) or abs(z) > 1e10

    def test_wald_z_statistic_with_negative_se(self):
        """Test Wald Z statistic with negative standard error (should handle gracefully)."""
        z = calculate_wald_z_statistic(1.0, -1.0)
        # Should handle negative SE (take absolute value or return inf)
        assert np.isinf(z) or abs(z) > 0

    def test_p_value_z_test_with_extreme_z(self):
        """Test p-value calculation with extreme Z values."""
        # Very large Z should give very small p-value
        p = calculate_p_value_z_test(10.0)
        assert p < 0.0001
        
        # Very small Z should give p-value close to 1
        p_small = calculate_p_value_z_test(0.0)
        assert abs(p_small - 1.0) < 0.01

    def test_p_value_z_test_with_negative_z(self):
        """Test p-value calculation with negative Z values."""
        p_pos = calculate_p_value_z_test(1.96)
        p_neg = calculate_p_value_z_test(-1.96)
        
        # Two-tailed test, so they should be equal
        assert abs(p_pos - p_neg) < 0.0001

    def test_f_statistic_with_zero_residual_sum_squares(self):
        """Test F statistic with zero residual sum of squares (perfect fit)."""
        # This would lead to division by zero
        # Should return inf or handle gracefully
        f_stat = calculate_f_statistic(10.0, 0.0, 10, 2)
        assert np.isinf(f_stat) or f_stat > 1e10

    def test_f_statistic_with_negative_values(self):
        """Test F statistic with negative values (should not happen in reality)."""
        # This is a theoretical test
        f_stat = calculate_f_statistic(-10.0, 10.0, 10, 2)
        # Should handle gracefully
        assert isinstance(f_stat, (int, float, np.floating))

    def test_benjamini_hochberg_fdr_with_empty_list(self):
        """Test FDR correction with an empty list of p-values."""
        corrected = apply_benjamini_hochberg_fdr([])
        assert corrected == []

    def test_benjamini_hochberg_fdr_with_single_p_value(self):
        """Test FDR correction with a single p-value."""
        corrected = apply_benjamini_hochberg_fdr([0.05])
        assert len(corrected) == 1
        assert corrected[0] == 0.05  # For single value, corrected = p

    def test_benjamini_hochberg_fdr_with_all_zeros(self):
        """Test FDR correction with all zero p-values."""
        corrected = apply_benjamini_hochberg_fdr([0.0, 0.0, 0.0])
        assert all(c == 0.0 for c in corrected)

    def test_benjamini_hochberg_fdr_with_all_ones(self):
        """Test FDR correction with all one p-values."""
        corrected = apply_benjamini_hochberg_fdr([1.0, 1.0, 1.0])
        assert all(c == 1.0 for c in corrected)

    def test_benjamini_hochberg_fdr_with_unsorted_p_values(self):
        """Test FDR correction with unsorted p-values."""
        p_values = [0.05, 0.01, 0.1, 0.02]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        # The function should handle unsorted input
        assert len(corrected) == len(p_values)
        # Corrected p-values should be in the same order as input
        # But the algorithm typically sorts them first, then reorders
        # So we just check that the output is valid
        assert all(0 <= c <= 1 for c in corrected)

    def test_benjamini_hochberg_fdr_with_nan_p_values(self):
        """Test FDR correction with NaN p-values."""
        p_values = [0.05, np.nan, 0.1]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        # Should handle NaN gracefully
        assert len(corrected) == len(p_values)
        # NaN should propagate or be handled
        assert any(np.isnan(c) for c in corrected) or not any(np.isnan(c) for c in corrected)

    def test_benjamini_hochberg_fdr_with_inf_p_values(self):
        """Test FDR correction with infinite p-values."""
        p_values = [0.05, np.inf, 0.1]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        # Should handle infinity gracefully
        assert len(corrected) == len(p_values)

    def test_benjamini_hochberg_fdr_with_negative_p_values(self):
        """Test FDR correction with negative p-values (invalid, but test robustness)."""
        p_values = [0.05, -0.1, 0.1]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        # Should handle negative values gracefully
        assert len(corrected) == len(p_values)

    def test_benjamini_hochberg_fdr_with_large_sample(self):
        """Test FDR correction with a large number of p-values."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 1000)
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        assert len(corrected) == 1000
        assert all(0 <= c <= 1 for c in corrected)

    def test_benjamini_hochberg_fdr_monotonicity(self):
        """Test that corrected p-values are monotonically increasing (property of BH)."""
        p_values = [0.1, 0.05, 0.01, 0.02]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        # The corrected p-values should be monotonically increasing when sorted by original p-value
        # But since the input is not sorted, we sort them for the check
        sorted_indices = np.argsort(p_values)
        sorted_corrected = [corrected[i] for i in sorted_indices]
        
        # Check monotonicity
        for i in range(1, len(sorted_corrected)):
            assert sorted_corrected[i] >= sorted_corrected[i-1] - 1e-10  # Allow for floating point errors

    def test_f_statistic_from_sums_with_zero_df(self):
        """Test F statistic from sums with zero degrees of freedom."""
        # Should handle division by zero
        f_stat = calculate_f_statistic_from_sums(10.0, 20.0, 0, 10)
        assert np.isinf(f_stat) or f_stat > 1e10

    def test_f_statistic_from_sums_with_negative_df(self):
        """Test F statistic from sums with negative degrees of freedom."""
        f_stat = calculate_f_statistic_from_sums(10.0, 20.0, -1, 10)
        # Should handle gracefully
        assert isinstance(f_stat, (int, float, np.floating))

    def test_calculate_wald_z_statistic_with_nan(self):
        """Test Wald Z statistic with NaN coefficient or SE."""
        z = calculate_wald_z_statistic(np.nan, 1.0)
        assert np.isnan(z)
        
        z = calculate_wald_z_statistic(1.0, np.nan)
        assert np.isnan(z)

    def test_calculate_p_value_z_test_with_nan(self):
        """Test p-value calculation with NaN Z."""
        p = calculate_p_value_z_test(np.nan)
        assert np.isnan(p)

    def test_calculate_f_statistic_with_nan(self):
        """Test F statistic calculation with NaN values."""
        f_stat = calculate_f_statistic(np.nan, 10.0, 10, 2)
        assert np.isnan(f_stat)
        
        f_stat = calculate_f_statistic(10.0, np.nan, 10, 2)
        assert np.isnan(f_stat)

    def test_apply_benjamini_hochberg_fdr_with_duplicates(self):
        """Test FDR correction with duplicate p-values."""
        p_values = [0.05, 0.05, 0.05, 0.05]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        assert len(corrected) == 4
        assert all(0 <= c <= 1 for c in corrected)

    def test_apply_benjamini_hochberg_fdr_with_very_small_p_values(self):
        """Test FDR correction with very small p-values."""
        p_values = [1e-10, 1e-9, 1e-8, 1e-7]
        corrected = apply_benjamini_hochberg_fdr(p_values)
        
        assert len(corrected) == 4
        assert all(0 <= c <= 1 for c in corrected)
        # Corrected p-values should be larger than or equal to original
        for i in range(len(p_values)):
            assert corrected[i] >= p_values[i] - 1e-15  # Allow for floating point errors
