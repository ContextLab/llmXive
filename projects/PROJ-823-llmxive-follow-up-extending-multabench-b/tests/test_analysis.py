"""
Unit tests for correlation analysis in User Story 3.
Specifically tests the correlation calculation logic and FDR correction.
"""
import unittest
import numpy as np
from scipy import stats
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.correlation import calculate_recovery_ratio, compute_pearson_correlation, perform_t_test
from analysis.fdr_correction import benjamini_hochberg


class TestCorrelationCalculation(unittest.TestCase):
    """Test cases for correlation calculation functions."""

    def test_recovery_ratio_calculation(self):
        """Test the Recovery Ratio formula: (CPU-Conditioned - Frozen_Aggregated) / (GPU-Tuned - Frozen_Aggregated)"""
        # Case 1: Standard positive recovery
        cpu_cond = 0.90
        frozen_agg = 0.80
        gpu_tuned = 1.00
        expected = (0.90 - 0.80) / (1.00 - 0.80)  # 0.10 / 0.20 = 0.5
        result = calculate_recovery_ratio(cpu_cond, frozen_agg, gpu_tuned)
        self.assertAlmostEqual(result, expected, places=5)

        # Case 2: No improvement over frozen (recovery = 0)
        result_zero = calculate_recovery_ratio(0.80, 0.80, 1.00)
        self.assertAlmostEqual(result_zero, 0.0, places=5)

        # Case 3: Perfect recovery (recovery = 1)
        result_perfect = calculate_recovery_ratio(1.00, 0.80, 1.00)
        self.assertAlmostEqual(result_perfect, 1.0, places=5)

        # Case 4: Negative recovery (worse than frozen)
        result_neg = calculate_recovery_ratio(0.70, 0.80, 1.00)
        expected_neg = -0.5
        self.assertAlmostEqual(result_neg, expected_neg, places=5)

    def test_recovery_ratio_division_by_zero(self):
        """Test that division by zero is handled when GPU-Tuned equals Frozen-Aggregated."""
        cpu_cond = 0.90
        frozen_agg = 0.80
        gpu_tuned = 0.80  # Denominator becomes 0

        with self.assertRaises(ZeroDivisionError):
            calculate_recovery_ratio(cpu_cond, frozen_agg, gpu_tuned)

    def test_pearson_correlation(self):
        """Test Pearson correlation calculation between two arrays."""
        # Perfect positive correlation
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r, p = compute_pearson_correlation(x, y)
        self.assertAlmostEqual(r, 1.0, places=5)
        self.assertLess(p, 0.05)

        # Perfect negative correlation
        y_neg = np.array([10, 8, 6, 4, 2])
        r_neg, p_neg = compute_pearson_correlation(x, y_neg)
        self.assertAlmostEqual(r_neg, -1.0, places=5)

        # No correlation (random noise)
        np.random.seed(42)
        y_noise = np.random.rand(100)
        r_noise, p_noise = compute_pearson_correlation(x[:100], y_noise)
        # We don't assert exact value, just that it runs and returns valid floats
        self.assertIsInstance(r_noise, float)
        self.assertIsInstance(p_noise, float)
        self.assertGreaterEqual(r_noise, -1.0)
        self.assertLessEqual(r_noise, 1.0)
        self.assertGreaterEqual(p_noise, 0.0)
        self.assertLessEqual(p_noise, 1.0)

    def test_t_test_calculation(self):
        """Test one-sample t-test implementation."""
        # Sample data where mean is significantly different from 0
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        hypothesized_mean = 0.0
        t_stat, p_val = perform_t_test(data, hypothesized_mean)

        # Verify t-statistic is positive (mean > hypothesized)
        self.assertGreater(t_stat, 0)
        # Verify p-value is very small for such a clear difference
        self.assertLess(p_val, 0.01)

        # Test against a mean that is exactly the sample mean (p should be 1.0)
        sample_mean = np.mean(data)
        t_stat_zero, p_val_zero = perform_t_test(data, sample_mean)
        self.assertAlmostEqual(t_stat_zero, 0.0, places=5)
        self.assertAlmostEqual(p_val_zero, 1.0, places=5)

    def test_correlation_with_empty_arrays(self):
        """Test handling of empty arrays."""
        x_empty = np.array([])
        y_empty = np.array([])

        with self.assertRaises(ValueError):
            compute_pearson_correlation(x_empty, y_empty)

        with self.assertRaises(ValueError):
            perform_t_test(x_empty, 0.0)

    def test_correlation_with_single_element(self):
        """Test handling of single element arrays (undefined correlation)."""
        x_single = np.array([1.0])
        y_single = np.array([2.0])

        # Correlation is undefined for single element
        with self.assertRaises(ValueError):
            compute_pearson_correlation(x_single, y_single)

        # T-test might run but variance is 0, leading to division by zero or similar
        # Depending on scipy version, this might raise or return nan
        t_stat, p_val = perform_t_test(x_single, 0.0)
        # If it doesn't crash, t-stat should be nan or inf
        self.assertTrue(np.isnan(t_stat) or np.isinf(t_stat))


class TestBenjaminiHochberg(unittest.TestCase):
    """Test cases for Benjamini-Hochberg FDR correction implementation."""

    def test_bh_basic_increasing_pvalues(self):
        """Test BH correction with a simple increasing list of p-values."""
        # Known example: p-values [0.01, 0.04, 0.03, 0.20, 0.15]
        # Sorted: [0.01, 0.03, 0.04, 0.15, 0.20]
        # Ranks: 1, 2, 3, 4, 5
        # Thresholds (alpha=0.05): 0.01, 0.02, 0.03, 0.04, 0.05
        # 0.01 <= 0.01 (Keep), 0.03 > 0.02 (Reject), 0.04 > 0.03 (Reject)...
        # Actually, the BH procedure finds the largest k such that p(k) <= (k/m)*alpha
        # Then rejects all hypotheses 1..k.
        p_values = np.array([0.01, 0.04, 0.03, 0.20, 0.15])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertEqual(len(q_values), 5)
        self.assertEqual(len(is_significant), 5)

        # Check that q-values are monotonically increasing with sorted p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        sorted_q = q_values[sorted_indices]
        
        # q-values should be >= corresponding p-values
        self.assertTrue(np.all(sorted_q >= sorted_p))
        
        # The q-values should be monotonically non-decreasing
        self.assertTrue(np.all(np.diff(sorted_q) >= -1e-10))  # Allow small float error

    def test_bh_all_significant(self):
        """Test case where all p-values are very small (all significant)."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertTrue(np.all(is_significant))
        # All q-values should be <= 0.05
        self.assertTrue(np.all(q_values <= 0.05))

    def test_bh_none_significant(self):
        """Test case where all p-values are large (none significant)."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertFalse(np.any(is_significant))
        # All q-values should be > 0.05
        self.assertTrue(np.all(q_values > 0.05))

    def test_bh_single_pvalue(self):
        """Test with a single p-value."""
        p_values = np.array([0.04])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertEqual(len(q_values), 1)
        self.assertTrue(is_significant[0])
        self.assertAlmostEqual(q_values[0], 0.04, places=5)  # For single value, q = p

    def test_bh_single_pvalue_not_significant(self):
        """Test with a single p-value that is not significant."""
        p_values = np.array([0.10])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertFalse(is_significant[0])
        self.assertAlmostEqual(q_values[0], 0.10, places=5)

    def test_bh_empty_array(self):
        """Test handling of empty array."""
        p_values = np.array([])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        self.assertEqual(len(q_values), 0)
        self.assertEqual(len(is_significant), 0)

    def test_bh_duplicate_pvalues(self):
        """Test with duplicate p-values."""
        p_values = np.array([0.01, 0.01, 0.01, 0.5, 0.5])
        q_values, is_significant = benjamini_hochberg(p_values, alpha=0.05)

        # The first three should likely be significant
        # The last two likely not
        # We check that the logic holds: q-values >= p-values
        self.assertTrue(np.all(q_values >= p_values))
        
        # Check monotonicity of q-values relative to sorted p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        sorted_q = q_values[sorted_indices]
        self.assertTrue(np.all(np.diff(sorted_q) >= -1e-10))

    def test_bh_alpha_parameter(self):
        """Test that the alpha parameter correctly affects significance."""
        p_values = np.array([0.04, 0.06, 0.08])
        
        # With alpha=0.05, only 0.04 might be significant (depending on rank)
        _, sig_05 = benjamini_hochberg(p_values, alpha=0.05)
        
        # With alpha=0.10, more might be significant
        _, sig_10 = benjamini_hochberg(p_values, alpha=0.10)
        
        # The number of significant results with alpha=0.10 should be >= alpha=0.05
        self.assertGreaterEqual(np.sum(sig_10), np.sum(sig_05))


if __name__ == '__main__':
    unittest.main()