"""
Unit tests for the statistical analysis module (src/analysis/stats.py).
"""

import pytest
import numpy as np
from src.analysis.stats import permute_test, bonferroni_correct


class TestPermuteTest:
    """Tests for the permutation test engine."""

    def test_permute_test_basic(self):
        """Test basic functionality with known distributions."""
        # Create two distinct distributions
        np.random.seed(42)
        data_a = np.random.normal(loc=10, scale=1.0, size=100)
        data_b = np.random.normal(loc=12, scale=1.0, size=100)

        p_val, obs_stat, null_dist = permute_test(
            data_a, data_b, n_iterations=1000, seed=42
        )

        # The means should be different (approx 2.0)
        assert np.abs(obs_stat - (-2.0)) < 0.5

        # The p-value should be small (< 0.05) given the separation
        assert p_val < 0.05

    def test_permute_test_identical_distributions(self):
        """Test that identical distributions yield high p-value."""
        np.random.seed(42)
        data = np.random.normal(loc=10, scale=1.0, size=100)

        p_val, _, _ = permute_test(data, data, n_iterations=1000, seed=42)

        # With identical data, p-value should be high (not significant)
        assert p_val > 0.05

    def test_permute_test_single_sided_greater(self):
        """Test one-sided alternative hypothesis."""
        np.random.seed(42)
        data_a = np.random.normal(loc=12, scale=1.0, size=100)
        data_b = np.random.normal(loc=10, scale=1.0, size=100)

        p_val, _, _ = permute_test(
            data_a, data_b, n_iterations=1000, alternative="greater", seed=42
        )

        # A > B should be significant for "greater"
        assert p_val < 0.05

    def test_permute_test_median_statistic(self):
        """Test with median difference statistic."""
        np.random.seed(42)
        data_a = np.random.normal(loc=10, scale=1.0, size=100)
        data_b = np.random.normal(loc=12, scale=1.0, size=100)

        p_val, obs_stat, _ = permute_test(
            data_a, data_b,
            n_iterations=1000,
            statistic_func="median_diff",
            seed=42
        )

        # Median difference should be approx -2
        assert np.abs(obs_stat - (-2.0)) < 0.5

    def test_permute_test_empty_input(self):
        """Test that empty inputs raise ValueError."""
        with pytest.raises(ValueError):
            permute_test([], [1, 2, 3])

    def test_permute_test_invalid_iterations(self):
        """Test that n_iterations < 1 raises ValueError."""
        with pytest.raises(ValueError):
            permute_test([1, 2], [3, 4], n_iterations=0)

    def test_permute_test_reproducibility(self):
        """Test that same seed yields same results."""
        np.random.seed(42)
        data_a = np.random.normal(loc=10, scale=1.0, size=50)
        data_b = np.random.normal(loc=12, scale=1.0, size=50)

        p1, s1, n1 = permute_test(data_a, data_b, n_iterations=500, seed=123)
        p2, s2, n2 = permute_test(data_a, data_b, n_iterations=500, seed=123)

        assert p1 == p2
        assert s1 == s2
        np.testing.assert_array_equal(n1, n2)


class TestBonferroniCorrect:
    """Tests for the Bonferroni correction logic."""

    def test_bonferroni_basic(self):
        """Test basic correction."""
        p_values = [0.01, 0.02, 0.05, 0.10]
        corrected, is_sig = bonferroni_correct(p_values)

        # Expected: p * 4
        expected = [0.04, 0.08, 0.20, 0.40]
        np.testing.assert_array_almost_equal(corrected, expected)

        # Only the first one (0.04) is < 0.05
        assert is_sig[0] is True
        assert is_sig[1] is False
        assert is_sig[2] is False
        assert is_sig[3] is False

    def test_bonferroni_capping(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.8]
        corrected, _ = bonferroni_correct(p_values, n_tests=3)

        assert np.all(corrected <= 1.0)

    def test_bonferroni_empty(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            bonferroni_correct([])

    def test_bonferroni_custom_n_tests(self):
        """Test with explicit n_tests different from array length."""
        p_values = [0.01, 0.02]
        # If we claim these are part of a family of 10 tests
        corrected, _ = bonferroni_correct(p_values, n_tests=10)

        # Expected: 0.01 * 10 = 0.1, 0.02 * 10 = 0.2
        assert np.isclose(corrected[0], 0.1)
        assert np.isclose(corrected[1], 0.2)