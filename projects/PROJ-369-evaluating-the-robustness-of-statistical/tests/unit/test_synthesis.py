"""
Unit tests for the synthesis module, specifically the shuffling functionality.
"""
import pytest
import numpy as np
import pandas as pd
from src.synthesis.generators import (
    shuffle_series,
    generate_null_distributions,
    compute_acf_lag1
)
from src.utils.config import set_seed

# Helper to compute ACF lag-1 for testing
def compute_acf_lag1(series: np.ndarray) -> float:
    n = len(series)
    if n < 2:
        return 0.0
    mean = np.mean(series)
    var = np.var(series)
    if var == 0:
        return 0.0
    return np.sum((series[:-1] - mean) * (series[1:] - mean)) / ((n - 1) * var)


class TestShuffling:
    def test_shuffle_preserves_values(self):
        """Test that shuffling preserves the set of values (marginal distribution)."""
        set_seed(42)
        original = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        shuffled = shuffle_series(original, seed=42)
        np.testing.assert_array_equal(sorted(original), sorted(shuffled))

    def test_shuffle_preserves_index(self):
        """Test that shuffling a pandas Series preserves the index."""
        set_seed(42)
        idx = pd.date_range('2020-01-01', periods=5)
        original = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
        shuffled = shuffle_series(original, seed=42)
        pd.testing.assert_index_equal(original.index, shuffled.index)

    def test_shuffle_destroys_autocorrelation(self):
        """Test that shuffling reduces autocorrelation to near zero."""
        set_seed(42)
        # Create a series with strong autocorrelation
        n = 1000
        eps = np.random.randn(n)
        autocorr_series = np.zeros(n)
        autocorr_series[0] = eps[0]
        for i in range(1, n):
            autocorr_series[i] = 0.9 * autocorr_series[i-1] + eps[i]

        original_acf = compute_acf_lag1(autocorr_series)
        shuffled = shuffle_series(autocorr_series, seed=42)
        shuffled_acf = compute_acf_lag1(shuffled)

        # Original should have high autocorrelation
        assert abs(original_acf) > 0.5, "Original series should have high autocorrelation"
        # Shuffled should have near-zero autocorrelation
        assert abs(shuffled_acf) < 0.1, "Shuffled series should have near-zero autocorrelation"

    def test_generate_null_distributions(self):
        """Test the generation of multiple null distributions."""
        set_seed(42)
        series = np.random.randn(100)
        n_shuffles = 10
        null_dist = generate_null_distributions([series], n_shuffles=n_shuffles, seed=42)

        assert len(null_dist) == 1
        assert len(null_dist[0]) == n_shuffles
        for shuffled in null_dist[0]:
            assert len(shuffled) == len(series)
            np.testing.assert_array_equal(sorted(series), sorted(shuffled))

    def test_null_distribution_acf_near_zero(self):
        """Verify that the mean ACF of the null distribution is near zero."""
        set_seed(42)
        # Create a persistent series
        n = 1000
        eps = np.random.randn(n)
        persistent = np.zeros(n)
        persistent[0] = eps[0]
        for i in range(1, n):
            persistent[i] = 0.8 * persistent[i-1] + eps[i]

        n_shuffles = 100
        null_dist = generate_null_distributions([persistent], n_shuffles=n_shuffles, seed=42)

        acfs = [compute_acf_lag1(s) for s in null_dist[0]]
        mean_acf = np.mean(acfs)

        # The mean ACF of shuffled data should be close to 0
        assert abs(mean_acf) < 0.05, f"Mean ACF of null distribution should be near 0, got {mean_acf}"

    def test_shuffle_with_pandas_series(self):
        """Test shuffling with a pandas Series."""
        set_seed(42)
        idx = pd.date_range('2020-01-01', periods=10)
        original = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], index=idx)
        shuffled = shuffle_series(original, seed=42)

        assert isinstance(shuffled, pd.Series)
        pd.testing.assert_index_equal(original.index, shuffled.index)
        np.testing.assert_array_equal(sorted(original.values), sorted(shuffled.values))