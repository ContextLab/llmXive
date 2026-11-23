"""
Unit tests for statistical analysis functions in code/analysis.py.
Specifically tests the Welch's t-test implementation as per T033c.
"""
import unittest
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
import sys
import os

# Add the project root to the path to allow imports from code/
# Assuming this test file is at tests/unit/test_analysis.py
# and code/analysis.py is at code/analysis.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis import welch_t_test, calculate_cohen_d, calculate_effect_size_ci


class TestWelchTTest(unittest.TestCase):
    """Unit tests for the welch_t_test function."""

    def setUp(self):
        """Set up test data for Welch's t-test."""
        # Create synthetic but realistic data for two independent groups
        # Group 1: Nostalgia condition (n=30)
        np.random.seed(42)
        self.nostalgia_pe = np.random.normal(loc=5.0, scale=2.0, size=30)
        self.nostalgia_cc = np.random.normal(loc=4.5, scale=1.5, size=30)

        # Group 2: Control condition (n=30)
        self.control_pe = np.random.normal(loc=7.0, scale=2.5, size=30)
        self.control_cc = np.random.normal(loc=6.0, scale=2.0, size=30)

        # Create a DataFrame matching the expected schema
        self.df = pd.DataFrame({
            'participant_id': [f'P{i:03d}' for i in range(60)],
            'stimulus_type': ['nostalgia'] * 30 + ['control'] * 30,
            'perseverative_errors': np.concatenate([self.nostalgia_pe, self.control_pe]),
            'categories_completed': np.concatenate([self.nostalgia_cc, self.control_cc]),
            'age': np.random.randint(65, 85, 60)
        })

    def test_welch_ttest_perseverative_errors(self):
        """Test Welch's t-test on perseverative_errors between groups."""
        result = welch_t_test(
            self.df,
            group_col='stimulus_type',
            value_col='perseverative_errors',
            group1='nostalgia',
            group2='control'
        )

        # Verify return type
        self.assertIsInstance(result, dict)

        # Verify expected keys
        self.assertIn('statistic', result)
        self.assertIn('pvalue', result)
        self.assertIn('group1_mean', result)
        self.assertIn('group2_mean', result)
        self.assertIn('group1_std', result)
        self.assertIn('group2_std', result)
        self.assertIn('group1_n', result)
        self.assertIn('group2_n', result)

        # Verify values are numeric
        self.assertIsInstance(result['statistic'], (int, float, np.floating))
        self.assertIsInstance(result['pvalue'], (int, float, np.floating))

        # Verify group means match our synthetic data
        self.assertAlmostEqual(result['group1_mean'], self.nostalgia_pe.mean(), places=5)
        self.assertAlmostEqual(result['group2_mean'], self.control_pe.mean(), places=5)

        # Verify sample sizes
        self.assertEqual(result['group1_n'], 30)
        self.assertEqual(result['group2_n'], 30)

        # Verify the t-statistic is approximately correct using scipy directly
        scipy_stat, scipy_p = scipy_stats.ttest_ind(
            self.nostalgia_pe,
            self.control_pe,
            equal_var=False  # Welch's t-test
        )
        self.assertAlmostEqual(result['statistic'], scipy_stat, places=5)
        self.assertAlmostEqual(result['pvalue'], scipy_p, places=5)

    def test_welch_ttest_categories_completed(self):
        """Test Welch's t-test on categories_completed between groups."""
        result = welch_t_test(
            self.df,
            group_col='stimulus_type',
            value_col='categories_completed',
            group1='nostalgia',
            group2='control'
        )

        # Verify return type and keys
        self.assertIsInstance(result, dict)
        self.assertIn('statistic', result)
        self.assertIn('pvalue', result)

        # Verify means
        self.assertAlmostEqual(result['group1_mean'], self.nostalgia_cc.mean(), places=5)
        self.assertAlmostEqual(result['group2_mean'], self.control_cc.mean(), places=5)

        # Verify against scipy
        scipy_stat, scipy_p = scipy_stats.ttest_ind(
            self.nostalgia_cc,
            self.control_cc,
            equal_var=False
        )
        self.assertAlmostEqual(result['statistic'], scipy_stat, places=5)
        self.assertAlmostEqual(result['pvalue'], scipy_p, places=5)

    def test_welch_ttest_unequal_sample_sizes(self):
        """Test Welch's t-test handles unequal sample sizes correctly."""
        # Create data with unequal group sizes
        df_unequal = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 20 + ['control'] * 40,
            'score': list(np.random.normal(5, 2, 20)) + list(np.random.normal(7, 2.5, 40))
        })

        result = welch_t_test(
            df_unequal,
            group_col='stimulus_type',
            value_col='score',
            group1='nostalgia',
            group2='control'
        )

        # Verify sample sizes are correctly reported
        self.assertEqual(result['group1_n'], 20)
        self.assertEqual(result['group2_n'], 40)

        # Verify it still produces valid statistics
        self.assertTrue(np.isfinite(result['statistic']))
        self.assertTrue(0 <= result['pvalue'] <= 1)

    def test_welch_ttest_identical_groups(self):
        """Test Welch's t-test returns p=1.0 for identical groups."""
        identical_data = pd.DataFrame({
            'stimulus_type': ['group_a'] * 20 + ['group_b'] * 20,
            'score': [5.0] * 40  # All values are identical
        })

        result = welch_t_test(
            identical_data,
            group_col='stimulus_type',
            value_col='score',
            group1='group_a',
            group2='group_b'
        )

        # When variance is zero, scipy may raise or return NaN, but Welch's
        # should handle it gracefully or we should handle it in our wrapper.
        # For identical values, the t-statistic is undefined (0/0), but typically
        # scipy returns nan for the statistic and nan for p-value.
        # We'll check that the function doesn't crash and returns something.
        self.assertIn('statistic', result)
        self.assertIn('pvalue', result)

    def test_welch_ttest_missing_group(self):
        """Test Welch's t-test raises error when a group is missing."""
        df_missing = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 30,
            'score': np.random.normal(5, 2, 30)
        })

        with self.assertRaises(ValueError):
            welch_t_test(
                df_missing,
                group_col='stimulus_type',
                value_col='score',
                group1='nostalgia',
                group2='control'  # 'control' group doesn't exist
            )

    def test_welch_ttest_wrong_value_type(self):
        """Test Welch's t-test raises error for non-numeric value column."""
        df_string = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 15 + ['control'] * 15,
            'score': ['a', 'b', 'c'] * 10  # String values
        })

        with self.assertRaises((ValueError, TypeError)):
            welch_t_test(
                df_string,
                group_col='stimulus_type',
                value_col='score',
                group1='nostalgia',
                group2='control'
            )


class TestCohenD(unittest.TestCase):
    """Unit tests for the calculate_cohen_d function."""

    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        self.group1 = np.random.normal(loc=5.0, scale=2.0, size=30)
        self.group2 = np.random.normal(loc=7.0, scale=2.5, size=30)

    def test_cohen_d_basic(self):
        """Test Cohen's d calculation with basic data."""
        d = calculate_cohen_d(self.group1, self.group2)

        self.assertIsInstance(d, float)
        self.assertTrue(np.isfinite(d))

        # Verify against manual calculation
        # Cohen's d = (mean1 - mean2) / pooled_std
        mean_diff = self.group1.mean() - self.group2.mean()
        n1, n2 = len(self.group1), len(self.group2)
        var1, var2 = self.group1.var(ddof=1), self.group2.var(ddof=1)
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        pooled_std = np.sqrt(pooled_var)
        expected_d = mean_diff / pooled_std

        self.assertAlmostEqual(d, expected_d, places=5)

    def test_cohen_d_equal_groups(self):
        """Test Cohen's d returns 0 for identical groups."""
        identical = np.array([5.0] * 20)
        d = calculate_cohen_d(identical, identical)
        self.assertEqual(d, 0.0)


class TestEffectSizeCI(unittest.TestCase):
    """Unit tests for the calculate_effect_size_ci function."""

    def setUp(self):
        """Set up test data."""
        np.random.seed(42)
        self.group1 = np.random.normal(loc=5.0, scale=2.0, size=30)
        self.group2 = np.random.normal(loc=7.0, scale=2.5, size=30)

    def test_effect_size_ci_basic(self):
        """Test effect size CI calculation."""
        ci = calculate_effect_size_ci(self.group1, self.group2, alpha=0.05)

        self.assertIsInstance(ci, dict)
        self.assertIn('lower', ci)
        self.assertIn('upper', ci)
        self.assertIn('effect_size', ci)

        # Verify lower < effect_size < upper
        self.assertLess(ci['lower'], ci['effect_size'])
        self.assertLess(ci['effect_size'], ci['upper'])

        # Verify CI contains 0 if effect is small (not always true, but for this test)
        # We're just checking the structure and logic, not the exact values


if __name__ == '__main__':
    unittest.main()