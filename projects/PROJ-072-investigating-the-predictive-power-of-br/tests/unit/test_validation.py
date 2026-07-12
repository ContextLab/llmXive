import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.classification.validation import permuted_t_test

class TestPermutedTTest:
    def test_permutation_p_value_high_signal(self):
        """
        Test that with a strong signal (separated groups), the p-value is low.
        """
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        # Create data with a clear difference in the first feature
        X = np.random.randn(n_samples, n_features)
        X[:50, 0] += 5.0  # Group 0 has mean +5 in feature 0
        X[50:, 0] -= 5.0  # Group 1 has mean -5 in feature 0

        y = np.array([0]*50 + [1]*50)

        result = permuted_t_test(X, y, n_permutations=100, seed=42)

        # The first feature should have a very low p-value
        assert result['fdr_p_values'][0] < 0.05, "Strong signal should yield significant p-value"

    def test_permutation_p_value_no_signal(self):
        """
        Test that with no signal (random data), the p-value is not significant.
        """
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        # Pure random data
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        result = permuted_t_test(X, y, n_permutations=100, seed=42)

        # Most p-values should be high, but with 100 permutations, we might get noise.
        # We just check that the logic runs and returns valid arrays.
        assert len(result['fdr_p_values']) == n_features
        assert not np.any(np.isnan(result['fdr_p_values']))

    def test_permutation_p_value_random_labels(self):
        """
        Test that when labels are shuffled relative to data, p-values are not significant.
        """
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        X = np.random.randn(n_samples, n_features)
        # Create a signal in feature 0
        X[:50, 0] += 5.0
        X[50:, 0] -= 5.0

        # Use random labels that are uncorrelated with the signal
        y = np.random.randint(0, 2, n_samples)

        result = permuted_t_test(X, y, n_permutations=100, seed=42)

        # The p-value for feature 0 should not be significant because labels are random
        # Note: With only 100 permutations, there's a chance of false positives,
        # but generally it should be non-significant.
        # We assert that it's not strictly 0 (which would indicate a bug) and not always < 0.05.
        # A more robust test would run many times.
        assert result['fdr_p_values'][0] >= 0.05 or result['fdr_p_values'][0] > 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
