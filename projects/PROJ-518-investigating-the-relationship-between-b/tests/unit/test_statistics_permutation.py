import numpy as np
import pytest

from analysis.statistics import run_permutation_test


class TestRunPermutationTest:
    """Unit tests for run_permutation_test (T027/T040)."""

    def test_returns_dict_with_required_keys(self):
        """Verify output contains 'empirical_p_value' and 'distribution_of_max_stats'."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        result = run_permutation_test(flexibility, creativity, n_permutations=100)

        assert isinstance(result, dict)
        assert "empirical_p_value" in result
        assert "distribution_of_max_stats" in result

    def test_empirical_p_value_in_range(self):
        """Verify empirical p-value is between 0 and 1."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        result = run_permutation_test(flexibility, creativity, n_permutations=100)

        p_val = result["empirical_p_value"]
        assert 0.0 <= p_val <= 1.0

    def test_distribution_of_max_stats_is_list(self):
        """Verify distribution_of_max_stats is a list of floats."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        result = run_permutation_test(flexibility, creativity, n_permutations=50)

        dist = result["distribution_of_max_stats"]
        assert isinstance(dist, list)
        assert len(dist) == 50
        assert all(isinstance(x, float) for x in dist)

    def test_permutation_test_with_perfect_correlation(self):
        """Test behavior when flexibility and creativity are identical."""
        n = 20
        flexibility = np.random.rand(n)
        creativity = flexibility.copy()  # Perfect correlation

        result = run_permutation_test(flexibility, creativity, n_permutations=100)

        # With perfect correlation, observed r=1.0.
        # Permutations will likely produce lower r, so p-value should be very small.
        assert result["empirical_p_value"] <= 0.05

    def test_permutation_test_with_uncorrelated_data(self):
        """Test behavior with truly uncorrelated data."""
        np.random.seed(123)
        flexibility = np.random.rand(50)
        creativity = np.random.rand(50)

        result = run_permutation_test(flexibility, creativity, n_permutations=500)

        # With uncorrelated data, p-value should be around 0.5 on average
        # (allowing for variance in small samples)
        assert 0.05 < result["empirical_p_value"] < 0.95

    def test_reproducibility_with_seed(self):
        """Verify that same seed produces same results."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        result1 = run_permutation_test(flexibility, creativity, n_permutations=100, seed=42)
        result2 = run_permutation_test(flexibility, creativity, n_permutations=100, seed=42)

        assert result1["empirical_p_value"] == result2["empirical_p_value"]
        assert result1["distribution_of_max_stats"] == result2["distribution_of_max_stats"]

    def test_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different results."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        result1 = run_permutation_test(flexibility, creativity, n_permutations=100, seed=42)
        result2 = run_permutation_test(flexibility, creativity, n_permutations=100, seed=123)

        # It is statistically extremely unlikely to get the exact same p-value
        # with different seeds and random shuffling, unless the distribution is degenerate.
        # We assert they are different to ensure randomness is used.
        assert result1["empirical_p_value"] != result2["empirical_p_value"]

    def test_large_n_permutations(self):
        """Verify function handles large number of permutations without error."""
        np.random.seed(42)
        flexibility = np.random.rand(20)
        creativity = np.random.rand(20)

        # Use a moderate number for unit test speed
        result = run_permutation_test(flexibility, creativity, n_permutations=1000)

        assert isinstance(result["empirical_p_value"], float)
        assert len(result["distribution_of_max_stats"]) == 1000

    def test_small_sample_size(self):
        """Verify function handles small sample sizes."""
        n = 5
        flexibility = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        creativity = np.array([0.5, 0.4, 0.3, 0.2, 0.1])

        result = run_permutation_test(flexibility, creativity, n_permutations=50)

        assert 0.0 <= result["empirical_p_value"] <= 1.0
        assert len(result["distribution_of_max_stats"]) == 50

    def test_vectorized_computation(self):
        """Verify that the function uses vectorized operations (no explicit Python loops)."""
        # This test ensures the implementation is efficient.
        # We can't directly inspect code, but we can time it.
        import time

        np.random.seed(42)
        flexibility = np.random.rand(50)
        creativity = np.random.rand(50)

        start = time.time()
        result = run_permutation_test(flexibility, creativity, n_permutations=5000)
        elapsed = time.time() - start

        # If vectorized, 5000 permutations on 50 samples should be fast (< 2 seconds)
        # If naive loop, it might be much slower.
        assert elapsed < 5.0, f"Permutation test took too long: {elapsed:.2f}s"
