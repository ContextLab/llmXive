import pytest
import numpy as np
import math
from scipy import stats as scipy_stats
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from stats import calculate_cohens_d, calculate_ci_95


class TestCohensDAndCI:
    """Unit tests for Cohen's d and 95% Confidence Interval calculations."""

    def test_cohens_d_basic(self):
        """Test Cohen's d calculation with known values."""
        # Group 1: [2, 4, 4, 4, 5, 5, 7, 9] -> mean=5, std=2.138
        group1 = np.array([2, 4, 4, 4, 5, 5, 7, 9])
        # Group 2: [1, 2, 3, 4, 5, 6, 7, 8] -> mean=4.5, std=2.449
        group2 = np.array([1, 2, 3, 4, 5, 6, 7, 8])

        d, pooled_std = calculate_cohens_d(group1, group2)

        # Expected calculation:
        # mean1 = 5.0, mean2 = 4.5
        # n1 = 8, n2 = 8
        # var1 = 4.5714, var2 = 6.0
        # pooled_var = ((7*4.5714 + 7*6.0) / 14) = 5.2857
        # pooled_std = sqrt(5.2857) = 2.299
        # d = (5.0 - 4.5) / 2.299 = 0.217

        expected_d = (np.mean(group1) - np.mean(group2)) / np.sqrt(
            ((len(group1) - 1) * np.var(group1, ddof=1) + (len(group2) - 1) * np.var(group2, ddof=1)) / (len(group1) + len(group2) - 2)
        )

        assert np.isclose(d, expected_d, rtol=1e-4)
        assert isinstance(d, float)

    def test_cohens_d_identical_groups(self):
        """Test Cohen's d is zero for identical groups."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1, 2, 3, 4, 5])

        d, _ = calculate_cohens_d(group1, group2)
        assert np.isclose(d, 0.0)

    def test_cohens_d_single_element(self):
        """Test handling of single element groups (should raise error or handle gracefully)."""
        # With N=1, std is 0 or undefined. Our implementation should handle this.
        group1 = np.array([1.0])
        group2 = np.array([2.0])

        # This should raise a ValueError because std is 0
        with pytest.raises(ValueError):
            calculate_cohens_d(group1, group2)

    def test_ci_95_basic(self):
        """Test 95% CI calculation for a mean."""
        data = np.array([10, 12, 13, 11, 14, 10, 12, 13])
        mean, lower, upper = calculate_ci_95(data)

        # Verify mean
        assert np.isclose(mean, np.mean(data))

        # Verify bounds (lower < mean < upper)
        assert lower < mean < upper

        # Verify width is reasonable (approx 2 * SEM * t_crit)
        n = len(data)
        sem = np.std(data, ddof=1) / np.sqrt(n)
        t_crit = scipy_stats.t.ppf(0.975, df=n-1)
        expected_margin = t_crit * sem

        assert np.isclose(upper - mean, expected_margin, rtol=1e-4)
        assert np.isclose(mean - lower, expected_margin, rtol=1e-4)

    def test_ci_95_single_element(self):
        """Test 95% CI for single element (should raise error)."""
        data = np.array([5.0])
        with pytest.raises(ValueError):
            calculate_ci_95(data)

    def test_ci_95_constant_data(self):
        """Test 95% CI for constant data (std=0)."""
        data = np.array([5.0, 5.0, 5.0, 5.0])
        mean, lower, upper = calculate_ci_95(data)

        assert np.isclose(mean, 5.0)
        assert np.isclose(lower, 5.0)
        assert np.isclose(upper, 5.0)

    def test_cohens_d_vs_scipy(self):
        """Compare our Cohen's d implementation with scipy (if available) or manual calc."""
        # Using a larger sample for better precision
        np.random.seed(42)
        group1 = np.random.normal(loc=10, scale=2, size=50)
        group2 = np.random.normal(loc=12, scale=2.5, size=50)

        d_manual, _ = calculate_cohens_d(group1, group2)

        # Manual calculation for verification
        mean1, mean2 = np.mean(group1), np.mean(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        expected_d = (mean1 - mean2) / np.sqrt(pooled_var)

        assert np.isclose(d_manual, expected_d, rtol=1e-5)