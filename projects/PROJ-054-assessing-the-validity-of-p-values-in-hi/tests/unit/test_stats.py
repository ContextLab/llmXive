"""
Unit tests for statistical analysis utilities.
Tests for code/analyze_pvalues.py and code/run_tests.py
"""
import numpy as np
import pytest
from scipy import stats
from analyze_pvalues import calculate_ks_statistic
from run_tests import run_hypothesis_tests


class TestHypothesisTests:
    def test_t_test_on_null_data(self):
        """Test t-test on data with no mean difference (null hypothesis true)."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        # Generate data with same mean for both groups
        group1 = np.random.randn(n_samples, n_features)
        group2 = np.random.randn(n_samples, n_features)

        p_values = run_hypothesis_tests(group1, group2)

        assert len(p_values) == n_features
        assert all(0 <= p <= 1 for p in p_values)

    def test_t_test_detects_mean_difference(self):
        """Test that t-test detects a mean difference."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        # Generate data with mean difference
        group1 = np.random.randn(n_samples, n_features)
        group2 = np.random.randn(n_samples, n_features) + 2.0  # Shift mean by 2

        p_values = run_hypothesis_tests(group1, group2)

        # Most p-values should be small
        assert np.mean(p_values) < 0.1

    def test_f_test_on_null_data(self):
        """Test F-test on data with equal variances (null hypothesis true)."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        # Generate data with same variance
        group1 = np.random.randn(n_samples, n_features)
        group2 = np.random.randn(n_samples, n_features)

        p_values = run_hypothesis_tests(group1, group2, test_type="f")

        assert len(p_values) == n_features
        assert all(0 <= p <= 1 for p in p_values)

    def test_f_test_detects_variance_difference(self):
        """Test that F-test detects a variance difference."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        # Generate data with variance difference
        group1 = np.random.randn(n_samples, n_features)
        group2 = np.random.randn(n_samples, n_features) * 2.0  # Double variance

        p_values = run_hypothesis_tests(group1, group2, test_type="f")

        # Most p-values should be small
        assert np.mean(p_values) < 0.1

    def test_invalid_test_type(self):
        """Test that invalid test type raises error."""
        group1 = np.random.randn(10, 5)
        group2 = np.random.randn(10, 5)

        with pytest.raises(ValueError):
            run_hypothesis_tests(group1, group2, test_type="invalid")

    def test_mismatched_dimensions(self):
        """Test that mismatched dimensions raise error."""
        group1 = np.random.randn(10, 5)
        group2 = np.random.randn(20, 5)

        with pytest.raises(ValueError):
            run_hypothesis_tests(group1, group2)


class TestKSStatistic:
    def test_uniform_pvalues(self):
        """Test KS statistic on uniformly distributed p-values."""
        np.random.seed(42)
        # Generate uniform p-values
        p_values = np.random.uniform(0, 1, 10000)

        ks_stat = calculate_ks_statistic(p_values)

        # For uniform distribution, KS statistic should be small
        assert ks_stat < 0.02

    def test_non_uniform_pvalues(self):
        """Test KS statistic on non-uniform p-values."""
        np.random.seed(42)
        # Generate p-values concentrated near 0 (anti-conservative)
        p_values = np.random.beta(0.5, 1, 10000)

        ks_stat = calculate_ks_statistic(p_values)

        # KS statistic should be larger
        assert ks_stat > 0.05

    def test_small_sample_size(self):
        """Test KS statistic with small sample size."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)

        ks_stat = calculate_ks_statistic(p_values)

        # Should still be calculable
        assert 0 <= ks_stat <= 1

    def test_ks_statistic_calculation(self):
        """Test that KS statistic is calculated correctly."""
        # Create known distribution
        p_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        ks_stat = calculate_ks_statistic(p_values)

        # Should be a valid KS statistic
        assert 0 <= ks_stat <= 1

        # Compare with scipy implementation
        scipy_ks = stats.kstest(p_values, 'uniform').statistic
        assert np.isclose(ks_stat, scipy_ks, rtol=1e-5)

    def test_empty_array(self):
        """Test KS statistic with empty array."""
        with pytest.raises(ValueError):
            calculate_ks_statistic(np.array([]))

    def test_single_value(self):
        """Test KS statistic with single value."""
        ks_stat = calculate_ks_statistic(np.array([0.5]))

        # Should be calculable
        assert 0 <= ks_stat <= 1

    def test_all_zeros(self):
        """Test KS statistic with all zeros."""
        p_values = np.zeros(100)
        ks_stat = calculate_ks_statistic(p_values)

        # Should be large (far from uniform)
        assert ks_stat > 0.5

    def test_all_ones(self):
        """Test KS statistic with all ones."""
        p_values = np.ones(100)
        ks_stat = calculate_ks_statistic(p_values)

        # Should be large (far from uniform)
        assert ks_stat > 0.5

def test_pvalue_collection_count():
    """Test that exactly p p-values are collected per iteration."""
    np.random.seed(42)
    n_samples = 100
    n_features = 50

    group1 = np.random.randn(n_samples, n_features)
    group2 = np.random.randn(n_samples, n_features)

    p_values = run_hypothesis_tests(group1, group2)

    assert len(p_values) == n_features

def test_pvalue_range():
    """Test that all p-values are in valid range [0, 1]."""
    np.random.seed(42)
    n_samples = 100
    n_features = 50

    group1 = np.random.randn(n_samples, n_features)
    group2 = np.random.randn(n_samples, n_features)

    p_values = run_hypothesis_tests(group1, group2)

    assert all(0 <= p <= 1 for p in p_values)

def test_kstest_against_uniform_reference():
    """Test KS statistic calculation against uniform reference."""
    np.random.seed(42)
    # Generate uniform p-values
    uniform_pvalues = np.random.uniform(0, 1, 10000)

    ks_stat_uniform = calculate_ks_statistic(uniform_pvalues)

    # Should be very small for uniform distribution
    assert ks_stat_uniform < 0.02

    # Generate non-uniform p-values (biased towards 0)
    biased_pvalues = np.random.beta(0.5, 1, 10000)

    ks_stat_biased = calculate_ks_statistic(biased_pvalues)

    # Biased should have larger KS statistic
    assert ks_stat_biased > ks_stat_uniform
