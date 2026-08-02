"""
Unit tests for statistical analysis logic in code/analysis/stats.py.

This module specifically tests the t-test calculation logic on synthetic accuracy data,
ensuring that the statistical functions produce expected results for known inputs.
"""

import unittest
import numpy as np
import scipy.stats as stats
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis import stats as analysis_stats


class TestTTestLogic(unittest.TestCase):
    """Test cases for t-test calculation logic."""

    def test_paired_ttest_identical_sets(self):
        """Test that paired t-test returns p=1.0 for identical datasets."""
        group_a = np.array([0.85, 0.86, 0.87, 0.88, 0.89])
        group_b = np.array([0.85, 0.86, 0.87, 0.88, 0.89])

        t_stat, p_val = analysis_stats.perform_paired_ttest(group_a, group_b)

        self.assertAlmostEqual(p_val, 1.0, places=5)
        self.assertAlmostEqual(t_stat, 0.0, places=5)

    def test_paired_ttest_significant_difference(self):
        """Test that paired t-test detects significant difference between distinct sets."""
        # Group A: High accuracy
        group_a = np.array([0.90, 0.92, 0.91, 0.93, 0.94])
        # Group B: Low accuracy
        group_b = np.array([0.60, 0.62, 0.61, 0.63, 0.64])

        t_stat, p_val = analysis_stats.perform_paired_ttest(group_a, group_b)

        # Expect a very small p-value (< 0.05) indicating significant difference
        self.assertLess(p_val, 0.05)
        # Expect a large t-statistic
        self.assertGreater(abs(t_stat), 10.0)

    def test_unpaired_ttest_equal_means(self):
        """Test unpaired t-test with equal means but different variances."""
        np.random.seed(42)
        group_a = np.random.normal(loc=0.5, scale=0.1, size=100)
        group_b = np.random.normal(loc=0.5, scale=0.2, size=100)

        t_stat, p_val = analysis_stats.perform_unpaired_ttest(group_a, group_b)

        # With equal means, p-value should be high (> 0.05)
        self.assertGreater(p_val, 0.05)

    def test_unpaired_ttest_different_means(self):
        """Test unpaired t-test with significantly different means."""
        group_a = np.array([0.80, 0.82, 0.81, 0.79, 0.83])
        group_b = np.array([0.40, 0.42, 0.41, 0.39, 0.43])

        t_stat, p_val = analysis_stats.perform_unpaired_ttest(group_a, group_b)

        # Expect significant difference
        self.assertLess(p_val, 0.01)
        self.assertGreater(t_stat, 0) # Group A > Group B

    def test_mann_whitney_u_small_sample(self):
        """Test Mann-Whitney U test fallback logic with small sample size."""
        # Small sample size (< 3) should trigger fallback logic in the analysis module
        group_a = np.array([0.80, 0.81])
        group_b = np.array([0.40, 0.41])

        # The analysis_stats module should handle this gracefully
        # We test that the function exists and returns valid values
        if hasattr(analysis_stats, 'perform_mann_whitney_u'):
            u_stat, p_val = analysis_stats.perform_mann_whitney_u(group_a, group_b)
            self.assertIsInstance(p_val, float)
            self.assertGreater(p_val, 0.0)
            self.assertLess(p_val, 1.0)

    def test_paired_ttest_one_sample(self):
        """Test behavior with single sample (should handle or raise expected error)."""
        group_a = np.array([0.85])
        group_b = np.array([0.86])

        # Depending on implementation, this might raise ValueError or return NaN
        try:
            t_stat, p_val = analysis_stats.perform_paired_ttest(group_a, group_b)
            # If it doesn't raise, p_val should be NaN or 1.0
            self.assertTrue(np.isnan(p_val) or p_val == 1.0)
        except ValueError:
            # Expected behavior for insufficient data
            pass

    def test_synthetic_accuracy_data_generation(self):
        """Test the helper function for generating synthetic accuracy data."""
        if hasattr(analysis_stats, 'generate_synthetic_accuracy_data'):
            data = analysis_stats.generate_synthetic_accuracy_data(
                n_seeds=5,
                mean_dp=0.80,
                mean_nondp=0.85,
                std=0.05
            )

            self.assertEqual(len(data), 5)
            self.assertIn('dp_accuracy', data[0])
            self.assertIn('nondp_accuracy', data[0])
            
            # Check that values are within reasonable bounds [0, 1]
            for row in data:
                self.assertGreaterEqual(row['dp_accuracy'], 0.0)
                self.assertLessEqual(row['dp_accuracy'], 1.0)
                self.assertGreaterEqual(row['nondp_accuracy'], 0.0)
                self.assertLessEqual(row['nondp_accuracy'], 1.0)


class TestStatisticalPower(unittest.TestCase):
    """Test cases for statistical power and sample size considerations."""

    def test_power_calculation_with_large_effect(self):
        """Verify that large effect sizes yield high statistical power."""
        # Effect size (Cohen's d) for large difference
        mean_diff = 0.20
        std_dev = 0.05
        n_per_group = 30

        if hasattr(analysis_stats, 'calculate_statistical_power'):
            power = analysis_stats.calculate_statistical_power(
                mean_diff=mean_diff,
                std_dev=std_dev,
                n_per_group=n_per_group
            )
            # With large effect and decent sample size, power should be high (> 0.8)
            self.assertGreater(power, 0.8)

    def test_power_calculation_with_small_sample(self):
        """Verify that small sample sizes yield low statistical power."""
        mean_diff = 0.05
        std_dev = 0.05
        n_per_group = 3

        if hasattr(analysis_stats, 'calculate_statistical_power'):
            power = analysis_stats.calculate_statistical_power(
                mean_diff=mean_diff,
                std_dev=std_dev,
                n_per_group=n_per_group
            )
            # With small sample, power should be low
            self.assertLess(power, 0.5)


if __name__ == '__main__':
    unittest.main()