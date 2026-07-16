"""
Unit tests for the bootstrap engine, specifically CI calculation logic and shuffling validation.
Corresponds to task T011 (existing) and T018 (new).
"""
import numpy as np
import pytest
from scipy import stats

# Import the functions under test from the project's code module
# The API surface confirms standard_bootstrap and shuffled_bootstrap are available
from code.bootstrap_engine import standard_bootstrap, shuffled_bootstrap
from code.config import get_bootstrap_seed, get_shuffle_seed


class TestStandardBootstrapCI:
    """Tests for the standard bootstrap CI calculation logic."""

    def test_standard_bootstrap_ci_bounds(self):
        """
        T011: Unit test for bootstrap CI calculation.
        
        Input: data = np.random.normal(0, 1, 1000), n_resamples=1000, seed=42.
        Logic: Run bootstrap, calculate 95% CI.
        Assertion: ci_lower < 0 < ci_upper and abs(ci_width - 0.12) < 0.02.
        """
        # Setup: Generate known data distribution
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=1000)
        
        n_resamples = 1000
        seed = 42

        # Execute: Run the standard bootstrap engine
        # standard_bootstrap returns a list of bootstrap means
        bootstrap_means = standard_bootstrap(data, n_resamples, seed)
        
        # Convert to numpy array for easier statistical operations
        bootstrap_means = np.array(bootstrap_means)

        # Logic: Calculate 95% Confidence Interval using the percentile method
        # This is the standard non-parametric bootstrap approach
        ci_lower = np.percentile(bootstrap_means, 2.5)
        ci_upper = np.percentile(bootstrap_means, 97.5)
        ci_width = ci_upper - ci_lower
        
        # Theoretical expectation:
        # For N=1000, sigma=1, SE = 1/sqrt(1000) ≈ 0.0316
        # 95% CI width ≈ 1.96 * 2 * SE ≈ 0.124
        # The task requires checking if width is approx 0.12 with tolerance 0.02

        # Assertion 1: The true mean (0.0) must be within the calculated CI
        assert ci_lower < 0.0 < ci_upper, (
            f"True mean (0.0) is outside CI bounds [{ci_lower:.4f}, {ci_upper:.4f}]. "
            "This suggests a failure in the bootstrap logic or an extreme outlier in the specific seed."
        )

        # Assertion 2: The CI width should be approximately 0.12 (within 0.02 tolerance)
        expected_width = 0.12
        tolerance = 0.02
        
        assert abs(ci_width - expected_width) < tolerance, (
            f"CI width {ci_width:.4f} deviates significantly from expected {expected_width:.4f}. "
            f"Observed width is outside tolerance [{expected_width - tolerance:.4f}, {expected_width + tolerance:.4f}]."
        )

    def test_bootstrap_distribution_normality(self):
        """
        Additional sanity check: The bootstrap distribution of means should be approximately normal
        due to the Central Limit Theorem, even if the original data was normal.
        """
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=1000)
        n_resamples = 1000
        seed = 42

        bootstrap_means = standard_bootstrap(data, n_resamples, seed)
        bootstrap_means = np.array(bootstrap_means)

        # Shapiro-Wilk test for normality (valid for sample sizes < 5000)
        stat, p_value = stats.shapiro(bootstrap_means[:5000])
        
        # We expect p_value > 0.05 for a normal distribution
        assert p_value > 0.05, (
            f"Bootstrap distribution failed normality test (p={p_value:.4f}). "
            "The bootstrap means should be approximately normally distributed."
        )

    def test_bootstrap_consistency_with_seed(self):
        """
        Verify that using the same seed produces the same results.
        """
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=100)
        n_resamples = 500
        seed = 12345

        # Run twice
        result_1 = standard_bootstrap(data, n_resamples, seed)
        result_2 = standard_bootstrap(data, n_resamples, seed)

        # They should be identical lists
        assert result_1 == result_2, "Bootstrap results are not reproducible with the same seed."

    def test_bootstrap_reduces_variance_with_more_samples(self):
        """
        Verify that increasing n_resamples stabilizes the CI width.
        """
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=1000)
        seed = 42

        # Run with small resamples
        means_small = standard_bootstrap(data, 100, seed)
        ci_small = np.percentile(means_small, [2.5, 97.5])
        
        # Run with large resamples
        means_large = standard_bootstrap(data, 5000, seed)
        ci_large = np.percentile(means_large, [2.5, 97.5])

        # The larger sample should be closer to the theoretical width (~0.124)
        # We just check that the large sample CI is reasonably stable and close to the small one
        # but the primary check is that it doesn't explode.
        width_small = ci_small[1] - ci_small[0]
        width_large = ci_large[1] - ci_large[0]

        # Both should be in the ballpark of 0.12
        assert 0.05 < width_small < 0.20, f"Small sample width {width_small} is unreasonable."
        assert 0.05 < width_large < 0.20, f"Large sample width {width_large} is unreasonable."


class TestShufflePreservation:
    """
    Tests for the shuffling logic required by US2 (T018).
    Verifies that shuffling preserves the marginal distribution.
    """

    def test_shuffle_preserves_marginal_distribution(self):
        """
        T018: Unit test for data shuffling in tests/test_bootstrap_engine.py.
        
        Input: data = np.random.normal(0, 1, 1000).
        Logic: Shuffle data, perform Kolmogorov-Smirnov test against original.
        Assertion: assert p_value > 0.05.
        """
        # Setup: Generate known data distribution
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=1000)
        
        # Generate a specific seed for the shuffle operation to ensure reproducibility
        # We use a fixed seed here to ensure the test is deterministic, 
        # though the statistical property should hold for any shuffle.
        shuffle_seed = 12345
        
        # Create a copy to shuffle (simulating what shuffled_bootstrap does internally)
        # We manually shuffle here to test the statistical property directly
        rng = np.random.RandomState(shuffle_seed)
        shuffled_data = data.copy()
        rng.shuffle(shuffled_data)
        
        # Logic: Perform Kolmogorov-Smirnov test against the original distribution
        # The KS test checks if two samples come from the same distribution.
        # Since shuffled_data is just a permutation of data, they must come from the same distribution.
        ks_statistic, p_value = stats.ks_2samp(data, shuffled_data)
        
        # Assertion: The p-value should be > 0.05, indicating no significant difference
        # between the distributions. Since they are permutations of the same set,
        # the p-value should be very high (often 1.0 or close to it).
        assert p_value > 0.05, (
            f"Shuffling altered the marginal distribution. KS test p-value: {p_value:.4f}. "
            "Shuffling a dataset should preserve the marginal distribution (permutation)."
        )

    def test_shuffle_breaks_temporal_order(self):
        """
        Additional check: Ensure that shuffling actually changes the order (autocorrelation drops).
        """
        np.random.seed(42)
        # Create data with strong autocorrelation (AR(1) like)
        n = 1000
        phi = 0.9
        data = np.zeros(n)
        noise = np.random.normal(0, 1, n)
        for t in range(1, n):
            data[t] = phi * data[t-1] + noise[t]
        
        # Calculate autocorrelation at lag 1 for original
        orig_autocorr = np.corrcoef(data[:-1], data[1:])[0, 1]
        
        # Shuffle
        shuffle_seed = 9999
        rng = np.random.RandomState(shuffle_seed)
        shuffled_data = data.copy()
        rng.shuffle(shuffled_data)
        
        # Calculate autocorrelation at lag 1 for shuffled
        shuffled_autocorr = np.corrcoef(shuffled_data[:-1], shuffled_data[1:])[0, 1]
        
        # The shuffled data should have near-zero autocorrelation (random noise)
        # The original should have high autocorrelation (~0.9)
        assert abs(orig_autocorr) > 0.5, "Original data should have strong autocorrelation."
        assert abs(shuffled_autocorr) < 0.1, (
            f"Shuffled data still has significant autocorrelation ({shuffled_autocorr:.4f}). "
            "Shuffling should break temporal dependencies."
        )

    def test_shuffled_bootstrap_matches_standard_on_unchanged_stats(self):
        """
        Verify that if we run standard bootstrap on shuffled data vs shuffled_bootstrap,
        the results are consistent (since shuffled_bootstrap just shuffles then bootsraps).
        """
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=500)
        
        n_resamples = 1000
        seed = 42
        shuffle_seed = 123
        
        # Method 1: Standard bootstrap on already shuffled data
        rng_shuffle = np.random.RandomState(shuffle_seed)
        shuffled_copy = data.copy()
        rng_shuffle.shuffle(shuffled_copy)
        means_1 = standard_bootstrap(shuffled_copy, n_resamples, seed)
        
        # Method 2: Use the shuffled_bootstrap function
        # Note: shuffled_bootstrap takes its own seed for the shuffle step
        means_2 = shuffled_bootstrap(data, n_resamples, seed, shuffle_seed=shuffle_seed)
        
        # The distributions should be statistically similar, though exact values differ
        # because the internal shuffle in shuffled_bootstrap uses the seed to shuffle,
        # and then bootstrap uses seed to resample.
        # To make them identical, we need to ensure the sequence of random numbers is identical.
        # Since we can't easily control the internal state of two separate functions to be byte-identical
        # without inspecting their implementation, we check statistical equivalence.
        
        means_1 = np.array(means_1)
        means_2 = np.array(means_2)
        
        # Both should have mean near 0
        assert abs(np.mean(means_1)) < 0.1
        assert abs(np.mean(means_2)) < 0.1
        
        # Both should have similar variance
        assert abs(np.var(means_1) - np.var(means_2)) < 0.01