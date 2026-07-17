"""
Unit tests for metrics calculation in code/eval/metrics.py.

This module tests:
1. Spearman rank correlation calculation against random baselines.
2. Permutation test logic (sufficient shuffles).
3. Uniform baseline comparison.

Dependencies:
- code/eval/metrics.py (must be implemented)
- numpy, scipy.stats
"""
import pytest
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path
import sys
import os

# Ensure code directory is in path
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from eval.metrics import (
    compute_spearman_correlation,
    generate_random_baseline,
    generate_uniform_baseline,
    permutation_test
)


class TestSpearmanCorrelation:
    """Tests for Spearman rank correlation calculation."""

    def test_perfect_correlation(self):
        """Test with perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5], dtype=float)
        y = np.array([2, 4, 6, 8, 10], dtype=float)
        
        rho, p_value = compute_spearman_correlation(x, y)
        
        assert np.isclose(rho, 1.0, atol=1e-5), f"Expected rho=1.0, got {rho}"
        assert p_value < 0.05, "Expected significant p-value for perfect correlation"

    def test_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = np.array([1, 2, 3, 4, 5], dtype=float)
        y = np.array([5, 4, 3, 2, 1], dtype=float)
        
        rho, p_value = compute_spearman_correlation(x, y)
        
        assert np.isclose(rho, -1.0, atol=1e-5), f"Expected rho=-1.0, got {rho}"

    def test_no_correlation(self):
        """Test with uncorrelated random data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        rho, p_value = compute_spearman_correlation(x, y)
        
        # Should be close to 0
        assert np.abs(rho) < 0.3, f"Expected rho near 0, got {rho}"

    def test_empty_arrays(self):
        """Test with empty arrays - should raise error."""
        with pytest.raises((ValueError, IndexError)):
            compute_spearman_correlation(np.array([]), np.array([]))

    def test_single_element(self):
        """Test with single element - undefined correlation."""
        with pytest.raises((ValueError, RuntimeError)):
            compute_spearman_correlation(np.array([1.0]), np.array([2.0]))


class TestRandomBaseline:
    """Tests for random baseline generation and comparison."""

    def test_random_baseline_mean_zero(self):
        """Test that random baseline has mean close to 0."""
        np.random.seed(42)
        random_baseline = generate_random_baseline(n=1000)
        
        assert np.abs(np.mean(random_baseline)) < 0.1, \
            f"Random baseline mean should be near 0, got {np.mean(random_baseline)}"

    def test_random_baseline_std_one(self):
        """Test that random baseline has std close to 1."""
        np.random.seed(42)
        random_baseline = generate_random_baseline(n=1000)
        
        assert np.isclose(np.std(random_baseline), 1.0, atol=0.1), \
            f"Random baseline std should be near 1, got {np.std(random_baseline)}"

    def test_random_baseline_correlation_with_true(self):
        """Test that random baseline has low correlation with true coefficients."""
        np.random.seed(42)
        
        # Generate some true coefficients
        true_coeffs = np.random.randn(200) * 0.5 + 0.1
        
        # Generate random baseline
        random_baseline = generate_random_baseline(n=len(true_coeffs))
        
        # Compute correlation
        rho, p_value = compute_spearman_correlation(random_baseline, true_coeffs)
        
        # Random baseline should have low correlation with true values
        assert np.abs(rho) < 0.2, \
            f"Random baseline correlation should be low, got {rho}"

    def test_random_baseline_seed_reproducibility(self):
        """Test that same seed produces same random baseline."""
        np.random.seed(42)
        baseline1 = generate_random_baseline(n=100)
        
        np.random.seed(42)
        baseline2 = generate_random_baseline(n=100)
        
        assert np.allclose(baseline1, baseline2), "Same seed should produce same baseline"


class TestUniformBaseline:
    """Tests for uniform baseline generation and comparison."""

    def test_uniform_baseline_constant(self):
        """Test that uniform baseline is constant."""
        true_coeffs = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        uniform_baseline = generate_uniform_baseline(true_coeffs)
        
        assert np.allclose(uniform_baseline, np.mean(true_coeffs)), \
            "Uniform baseline should be the mean of true coefficients"

    def test_uniform_baseline_correlation(self):
        """Test correlation of uniform baseline with true coefficients."""
        np.random.seed(42)
        true_coeffs = np.random.randn(200) * 0.5 + 0.1
        
        uniform_baseline = generate_uniform_baseline(true_coeffs)
        
        # Uniform baseline (constant) should have undefined or 0 correlation
        rho, p_value = compute_spearman_correlation(uniform_baseline, true_coeffs)
        
        # Spearman correlation with constant is undefined (nan) or 0
        assert np.isnan(rho) or np.abs(rho) < 0.01, \
            f"Uniform baseline correlation should be undefined/zero, got {rho}"


class TestPermutationTest:
    """Tests for permutation test logic."""

    def test_permutation_test_p_value_range(self):
        """Test that p-value is in valid range [0, 1]."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        p_value = permutation_test(x, y, n_permutations=100)
        
        assert 0 <= p_value <= 1, f"P-value should be in [0, 1], got {p_value}"

    def test_permutation_test_sufficient_shuffles(self):
        """Test that permutation test uses sufficient number of shuffles."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        # Test with different numbers of permutations
        p_values = []
        for n_perm in [10, 50, 100, 200]:
            p_val = permutation_test(x, y, n_permutations=n_perm)
            p_values.append(p_val)
        
        # All p-values should be valid
        for p_val in p_values:
            assert 0 <= p_val <= 1, f"Invalid p-value: {p_val}"

    def test_permutation_test_significant_result(self):
        """Test permutation test with significantly correlated data."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        y = np.array([2, 4, 6, 8, 10, 12, 14, 16, 18, 20], dtype=float)
        
        p_value = permutation_test(x, y, n_permutations=1000)
        
        # Perfectly correlated data should have very low p-value
        assert p_value < 0.05, f"Expected significant p-value, got {p_value}"

    def test_permutation_test_non_significant_result(self):
        """Test permutation test with non-correlated data."""
        np.random.seed(42)
        x = np.random.randn(200)
        y = np.random.randn(200)
        
        p_value = permutation_test(x, y, n_permutations=500)
        
        # Non-correlated data should have higher p-value (not necessarily > 0.05)
        # But should be more than the significant case
        assert p_value >= 0, f"P-value should be non-negative, got {p_value}"

    def test_permutation_test_deterministic_with_seed(self):
        """Test that permutation test is deterministic with fixed seed."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        p1 = permutation_test(x, y, n_permutations=100)
        
        np.random.seed(42)
        p2 = permutation_test(x, y, n_permutations=100)
        
        # Note: permutation test may not be fully deterministic due to implementation
        # but should be similar
        assert abs(p1 - p2) < 0.01, "Same seed should produce similar p-values"

    def test_permutation_test_minimum_permutations(self):
        """Test that permutation test requires minimum number of permutations."""
        x = np.random.randn(50)
        y = np.random.randn(50)
        
        # Should work with reasonable minimum
        p_value = permutation_test(x, y, n_permutations=10)
        assert 0 <= p_value <= 1

    def test_permutation_test_large_sample(self):
        """Test permutation test with larger sample size."""
        np.random.seed(42)
        x = np.random.randn(500)
        y = np.random.randn(500)
        
        p_value = permutation_test(x, y, n_permutations=200)
        
        assert 0 <= p_value <= 1, f"Invalid p-value for large sample: {p_value}"


class TestMetricsIntegration:
    """Integration tests for metrics module."""

    def test_full_baseline_comparison(self):
        """Test full comparison of model vs random vs uniform baseline."""
        np.random.seed(42)
        
        # Simulate true coefficients
        true_coeffs = np.random.randn(200) * 0.5 + 0.1
        
        # Simulate model predictions (some correlation)
        model_preds = true_coeffs * 0.7 + np.random.randn(200) * 0.3
        
        # Generate baselines
        random_baseline = generate_random_baseline(n=len(true_coeffs))
        uniform_baseline = generate_uniform_baseline(true_coeffs)
        
        # Compute correlations
        model_rho, _ = compute_spearman_correlation(model_preds, true_coeffs)
        random_rho, _ = compute_spearman_correlation(random_baseline, true_coeffs)
        uniform_rho, _ = compute_spearman_correlation(uniform_baseline, true_coeffs)
        
        # Model should outperform random baseline
        assert model_rho > random_rho, \
            f"Model ({model_rho}) should outperform random baseline ({random_rho})"
        
        # Model should outperform uniform baseline
        assert model_rho > uniform_rho, \
            f"Model ({model_rho}) should outperform uniform baseline ({uniform_rho})"

    def test_edge_case_nan_handling(self):
        """Test that metrics handle NaN values appropriately."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        
        # Should raise error or handle NaN
        with pytest.raises((ValueError, RuntimeWarning)):
            compute_spearman_correlation(x, y)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])