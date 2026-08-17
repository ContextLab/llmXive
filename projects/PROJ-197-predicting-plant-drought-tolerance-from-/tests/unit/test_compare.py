"""
Unit tests for the paired t-test functionality in code/models/compare.py.

This test validates the statistical comparison logic using synthetic but
realistic CV score arrays, ensuring the t-test implementation correctly
calculates p-values and handles edge cases.
"""

import pytest
import numpy as np
from scipy import stats

# Import the paired t-test function from the stats utility module
# Note: We import from utils.stats as defined in the API surface,
# rather than directly from models.compare, to test the core statistical logic.
from code.utils.stats import paired_ttest


class TestPairedTTest:
    """Test suite for the paired_ttest function."""

    def test_identical_scores_returns_zero_statistic(self):
        """
        When two models have identical CV scores, the t-statistic should be 0
        and the p-value should be 1.0 (or very close to it).
        """
        scores_a = np.array([0.85, 0.86, 0.84, 0.87, 0.85])
        scores_b = np.array([0.85, 0.86, 0.84, 0.87, 0.85])

        t_stat, p_value = paired_ttest(scores_a, scores_b)

        assert t_stat == 0.0
        assert p_value == 1.0

    def test_significant_difference_detected(self):
        """
        Test that a significant difference in means is detected.
        Model A has consistently higher scores than Model B.
        """
        # Synthetic CV scores for Model A (RandomForest)
        scores_a = np.array([0.90, 0.92, 0.89, 0.91, 0.93])
        # Synthetic CV scores for Model B (XGBoost) - slightly lower
        scores_b = np.array([0.82, 0.84, 0.81, 0.83, 0.85])

        t_stat, p_value = paired_ttest(scores_a, scores_b)

        # The difference is large, so p-value should be very small (< 0.05)
        assert p_value < 0.05
        # t-statistic should be positive (A > B)
        assert t_stat > 0

    def test_no_significant_difference(self):
        """
        Test that small random differences do not trigger significance.
        Scores are drawn from similar distributions.
        """
        np.random.seed(42)
        # Two sets of scores with overlapping distributions
        scores_a = np.random.normal(loc=0.85, scale=0.02, size=20)
        scores_b = np.random.normal(loc=0.86, scale=0.02, size=20)

        t_stat, p_value = paired_ttest(scores_a, scores_b)

        # With such small differences and variance, p-value should likely be > 0.05
        # (Note: stochastic, but highly likely given the setup)
        assert p_value > 0.05

    def test_single_sample(self):
        """
        Test behavior with a single data point (edge case).
        A t-test with n=1 is mathematically undefined (division by zero in std dev).
        The function should handle this gracefully, likely returning NaN or raising.
        Based on scipy.stats.ttest_rel behavior, it returns NaN for n=1.
        """
        scores_a = np.array([0.85])
        scores_b = np.array([0.86])

        t_stat, p_value = paired_ttest(scores_a, scores_b)

        # scipy.stats.ttest_rel returns (nan, nan) for n=1
        assert np.isnan(t_stat)
        assert np.isnan(p_value)

    def test_array_mismatch_raises_error(self):
        """
        Test that passing arrays of different lengths raises an error.
        """
        scores_a = np.array([0.85, 0.86, 0.87])
        scores_b = np.array([0.82, 0.84])

        with pytest.raises(ValueError):
            paired_ttest(scores_a, scores_b)

    def test_realistic_cv_scores_comparison(self):
        """
        Test with a more realistic set of 5-fold CV scores.
        Simulates a scenario where Model A (RF) slightly outperforms Model B (XGBoost).
        """
        # 5-fold CV scores
        scores_rf = np.array([0.78, 0.82, 0.79, 0.81, 0.80])
        scores_xgb = np.array([0.76, 0.79, 0.77, 0.78, 0.77])

        t_stat, p_value = paired_ttest(scores_rf, scores_xgb)

        # Verify the function returns valid floats
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)

        # In this specific synthetic case, the difference is consistent.
        # We expect a significant result or at least a calculated statistic.
        assert not np.isnan(p_value)

    def test_input_types(self):
        """
        Ensure the function accepts both lists and numpy arrays.
        """
        list_a = [0.8, 0.85, 0.82]
        list_b = [0.75, 0.78, 0.76]
        arr_a = np.array(list_a)
        arr_b = np.array(list_b)

        # List inputs
        t1, p1 = paired_ttest(list_a, list_b)
        # Array inputs
        t2, p2 = paired_ttest(arr_a, arr_b)

        # Results should be equivalent
        assert np.isclose(t1, t2)
        assert np.isclose(p1, p2)