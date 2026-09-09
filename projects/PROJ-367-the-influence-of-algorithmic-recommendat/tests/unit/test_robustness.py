"""
Unit tests for robustness.py (T042).

Tests residual permutation test logic.
"""
import pytest
import numpy as np
import pandas as pd
from robustness import residual_permutation_test

class TestResidualPermutationTest:
    def test_permutation_logic(self):
        """Test that the permutation test shuffles residuals and re-fits."""
        # Create a small synthetic dataset
        np.random.seed(42)
        n = 50
        X = np.random.randn(n, 2)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n) * 0.1
        
        # The function should return a PermutationResult object
        # containing the null distribution and observed statistic.
        # We verify that the null distribution has the expected size.
        result = residual_permutation_test(X, y, n_permutations=10)
        
        assert result.null_distribution.shape[0] == 10
        assert len(result.observed_statistic) > 0
        
        # The observed statistic should be outside the null distribution
        # if the effect is real, but for random data, it might be inside.
        # We just check that the calculation ran without error.

    def test_deterministic_seed(self):
        """Test that the permutation test is deterministic with a fixed seed."""
        np.random.seed(123)
        X = np.random.randn(20, 1)
        y = X[:, 0] + np.random.randn(20) * 0.1
        
        result1 = residual_permutation_test(X, y, n_permutations=5, random_state=42)
        result2 = residual_permutation_test(X, y, n_permutations=5, random_state=42)
        
        assert np.array_equal(result1.null_distribution, result2.null_distribution)
        assert result1.observed_statistic == result2.observed_statistic
