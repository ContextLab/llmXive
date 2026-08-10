"""
Unit tests for hypothesis test execution in run_tests.py.
These tests verify t-test and F-test execution on null data.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from run_tests import run_hypothesis_tests
from utils.exceptions import HypothesisTestError


class TestHypothesisTestExecution:
    """Tests for T020: t-test/F-test execution on null data."""

    def test_t_test_null_hypothesis(self):
        """Test that t-test correctly identifies null hypothesis for identical groups."""
        np.random.seed(42)
        n = 100
        # Create two identical groups (null hypothesis is true)
        group1 = np.random.normal(0, 1, n)
        group2 = group1.copy()  # Identical

        t_stat, p_value = run_hypothesis_tests(group1, group2, test_type='t')

        assert p_value > 0.05, f"P-value {p_value} should be > 0.05 for identical groups"
        assert 0 <= p_value <= 1, "P-value should be in [0, 1]"

    def test_f_test_null_hypothesis(self):
        """Test that F-test correctly identifies null hypothesis for equal variances."""
        np.random.seed(42)
        n = 100
        # Create two groups with equal variance
        group1 = np.random.normal(0, 1, n)
        group2 = np.random.normal(0, 1, n)

        f_stat, p_value = run_hypothesis_tests(group1, group2, test_type='f')

        assert p_value > 0.05, f"P-value {p_value} should be > 0.05 for equal variances"
        assert 0 <= p_value <= 1, "P-value should be in [0, 1]"

    def test_t_test_detects_mean_difference(self):
        """Test that t-test detects true mean difference."""
        np.random.seed(42)
        n = 100
        # Create groups with different means
        group1 = np.random.normal(0, 1, n)
        group2 = np.random.normal(1.0, 1, n)  # Mean difference of 1.0

        t_stat, p_value = run_hypothesis_tests(group1, group2, test_type='t')

        # With large effect size, should detect difference
        assert p_value < 0.05, f"P-value {p_value} should be < 0.05 for different means"

    def test_f_test_detects_variance_difference(self):
        """Test that F-test detects true variance difference."""
        np.random.seed(42)
        n = 100
        # Create groups with different variances
        group1 = np.random.normal(0, 1, n)
        group2 = np.random.normal(0, 2, n)  # Variance difference (std=2 vs std=1)

        f_stat, p_value = run_hypothesis_tests(group1, group2, test_type='f')

        # Should detect variance difference
        assert p_value < 0.05, f"P-value {p_value} should be < 0.05 for different variances"

    def test_collects_all_pvalues(self):
        """Test that all p-values are collected without missing values."""
        np.random.seed(42)
        n = 50
        p = 10  # Number of features

        # Create data matrix
        data = np.random.normal(0, 1, (n, p))

        # Run tests on all features
        pvalues = []
        for i in range(p):
            t_stat, pval = run_hypothesis_tests(data[:, i], data[:, i], test_type='t')
            pvalues.append(pval)

        # Verify all p-values are collected
        assert len(pvalues) == p, f"Should collect {p} p-values, got {len(pvalues)}"
        assert not any(np.isnan(pvalues)), "No p-values should be NaN"
        assert all(0 <= pv <= 1 for pv in pvalues), "All p-values should be in [0, 1]"

    def test_invalid_test_type(self):
        """Test that invalid test type raises appropriate error."""
        np.random.seed(42)
        group1 = np.random.normal(0, 1, 100)
        group2 = np.random.normal(0, 1, 100)

        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(group1, group2, test_type='invalid')

    def test_empty_groups(self):
        """Test that empty groups raise appropriate error."""
        group1 = np.array([])
        group2 = np.array([])

        with pytest.raises((ValueError, HypothesisTestError)):
            run_hypothesis_tests(group1, group2, test_type='t')
