"""
Unit tests for the run_hypothesis_tests function in code/run_tests.py.

These tests verify that:
1. T-tests and F-tests are executed correctly on known data
2. P-values are collected for all features
3. Error handling works for invalid inputs
4. The function handles edge cases (zero variance, small samples)
"""
import numpy as np
import pytest
from scipy import stats

from run_tests import run_hypothesis_tests
from utils.exceptions import HypothesisTestError


class TestRunHypothesisTests:
    """Tests for the run_hypothesis_tests function."""

    def test_basic_t_test_correctness(self):
        """Test that t-test produces correct results on a simple case."""
        # Create data with a known difference in means
        np.random.seed(123)
        n = 50
        # Group 0: mean = 0, Group 1: mean = 1
        data = np.vstack([
            np.random.normal(0, 1, (n, 1)),
            np.random.normal(1, 1, (n, 1))
        ])
        group_indices = np.array([0] * n + [1] * n)

        results = run_hypothesis_tests(data, group_indices=group_indices)

        # Check that we get results for the single feature
        assert results['t_pvalues'].shape == (1,)
        assert results['f_pvalues'].shape == (1,)

        # The p-value should be small (significant difference)
        # We expect p < 0.05 for a true difference
        assert results['t_pvalues'][0] < 0.05, \
            f"Expected significant p-value, got {results['t_pvalues'][0]}"

        # The t-statistic should be positive (mean1 > mean0)
        assert results['t_statistics'][0] > 0

    def test_null_hypothesis_uniform_pvalues(self):
        """Test that under the null hypothesis, p-values are roughly uniform."""
        np.random.seed(456)
        n_samples = 200
        n_features = 100

        # Both groups from the same distribution
        data = np.random.normal(0, 1, (n_samples, n_features))
        group_indices = np.random.randint(0, 2, n_samples)

        results = run_hypothesis_tests(data, group_indices=group_indices)

        # Under null, ~5% of p-values should be < 0.05
        alpha = 0.05
        observed_proportion = np.mean(results['t_pvalues'] < alpha)

        # With 100 features, we expect ~5 rejections. Allow some variance.
        # Using a wide confidence interval for small sample
        expected = alpha * n_features
        observed = observed_proportion * n_features

        # Should be within a reasonable range (e.g., 2x the expected)
        assert 0.5 * expected <= observed <= 2.0 * expected, \
            f"Observed {observed} rejections, expected ~{expected}"

    def test_f_test_variance_detection(self):
        """Test that F-test detects variance differences."""
        np.random.seed(789)
        n = 50
        # Group 0: variance = 1, Group 1: variance = 4
        data = np.vstack([
            np.random.normal(0, 1, (n, 1)),
            np.random.normal(0, 2, (n, 1))  # std=2 => var=4
        ])
        group_indices = np.array([0] * n + [1] * n)

        results = run_hypothesis_tests(data, group_indices=group_indices)

        # F-statistic should be large (variance ratio ~ 4)
        assert results['f_statistics'][0] > 2.0, \
            f"Expected large F-statistic, got {results['f_statistics'][0]}"

        # P-value should be small (significant variance difference)
        assert results['f_pvalues'][0] < 0.05, \
            f"Expected significant F-test p-value, got {results['f_pvalues'][0]}"

    def test_missing_group_indices_inference(self):
        """Test that group indices are inferred correctly when not provided."""
        np.random.seed(101)
        data = np.random.normal(0, 1, (100, 10))

        # Run without group_indices
        results = run_hypothesis_tests(data)

        # Should work without errors
        assert 't_pvalues' in results
        assert 'f_pvalues' in results
        assert results['t_pvalues'].shape == (10,)

    def test_invalid_data_dimensions(self):
        """Test error handling for invalid data dimensions."""
        # 1D array should fail
        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(np.array([1, 2, 3, 4, 5]))

        # 3D array should fail
        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(np.random.rand(10, 10, 10))

    def test_insufficient_samples(self):
        """Test error handling for insufficient samples."""
        # Only 1 sample
        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(np.random.rand(1, 10))

        # Only 1 sample per group
        data = np.random.rand(2, 10)
        group_indices = np.array([0, 1])
        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(data, group_indices=group_indices)

    def test_zero_variance_handling(self):
        """Test handling of features with zero variance."""
        np.random.seed(202)
        n = 50
        # Create data where one feature has zero variance in group 0
        data = np.random.normal(0, 1, (2 * n, 2))
        data[:n, 0] = 0  # Zero variance in group 0 for feature 0

        group_indices = np.array([0] * n + [1] * n)

        # Should not raise an error
        results = run_hypothesis_tests(data, group_indices=group_indices)

        # F-statistic for feature 0 should be inf (or very large)
        # P-value should be 0 (or very small)
        assert np.isinf(results['f_statistics'][0]) or results['f_statistics'][0] > 100

    def test_output_structure(self):
        """Test that the output contains all required keys with correct shapes."""
        np.random.seed(303)
        data = np.random.normal(0, 1, (100, 20))
        group_indices = np.random.randint(0, 2, 100)

        results = run_hypothesis_tests(data, group_indices=group_indices)

        expected_keys = {'t_pvalues', 'f_pvalues', 't_statistics', 'f_statistics'}
        assert set(results.keys()) == expected_keys

        n_features = 20
        assert results['t_pvalues'].shape == (n_features,)
        assert results['f_pvalues'].shape == (n_features,)
        assert results['t_statistics'].shape == (n_features,)
        assert results['f_statistics'].shape == (n_features,)

        # P-values should be in [0, 1]
        assert np.all(results['t_pvalues'] >= 0)
        assert np.all(results['t_pvalues'] <= 1)
        assert np.all(results['f_pvalues'] >= 0)
        assert np.all(results['f_pvalues'] <= 1)

    def test_custom_group_indices(self):
        """Test with custom group indices that are not balanced."""
        np.random.seed(404)
        n_samples = 100
        n_features = 10

        # Unbalanced groups: 30 in group 0, 70 in group 1
        group_indices = np.array([0] * 30 + [1] * 70)
        data = np.random.normal(0, 1, (n_samples, n_features))

        results = run_hypothesis_tests(data, group_indices=group_indices)

        # Should work without errors
        assert results['t_pvalues'].shape == (n_features,)
        assert results['f_pvalues'].shape == (n_features,)

    def test_invalid_group_indices_values(self):
        """Test error handling for invalid group index values."""
        data = np.random.rand(100, 10)
        group_indices = np.array([0, 1, 2] * 33 + [0])  # Contains 2

        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(data, group_indices=group_indices)

    def test_invalid_group_indices_shape(self):
        """Test error handling for mismatched group indices shape."""
        data = np.random.rand(100, 10)
        group_indices = np.array([0, 1] * 40)  # Wrong length

        with pytest.raises(HypothesisTestError):
            run_hypothesis_tests(data, group_indices=group_indices)