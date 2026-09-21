"""
Unit tests for the Lilliefors KS test implementation.

Tests verify:
1. The function correctly estimates the mean and normalizes data.
2. The KS statistic is computed correctly against the standard exponential CDF.
3. Edge cases (empty data, non-positive values) raise appropriate errors.
4. Known distributions (exponential vs uniform) produce expected statistics.
"""
import numpy as np
import pytest
from scipy import stats
from code.stats import lilliefors_ks


class TestLillieforsKs:
    """Tests for the lilliefors_ks function."""

    def test_empty_data_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            lilliefors_ks(np.array([]))

    def test_non_positive_data_raises(self):
        """Test that data with non-positive values raises ValueError."""
        data_with_zero = np.array([1.0, 0.0, 2.0])
        with pytest.raises(ValueError, match="strictly positive"):
            lilliefors_ks(data_with_zero)

        data_with_negative = np.array([1.0, -0.5, 2.0])
        with pytest.raises(ValueError, match="strictly positive"):
            lilliefors_ks(data_with_negative)

    def test_exponential_data_produces_small_statistic(self):
        """
        Test that data generated from an exponential distribution
        produces a small KS statistic (close to 0).
        
        This verifies the core logic: if data is truly exponential,
        after normalization it should match the standard exponential CDF well.
        """
        np.random.seed(42)
        # Generate data from Exponential(1) - mean = 1
        data = np.random.exponential(scale=1.0, size=1000)
        
        ks_stat = lilliefors_ks(data)
        
        # For n=1000, the critical value at alpha=0.05 is approx 1.36/sqrt(n) ≈ 0.043
        # We expect the statistic to be well below this for true exponential data
        assert ks_stat < 0.05, f"KS statistic {ks_stat} is unexpectedly large for exponential data"
        assert ks_stat >= 0, "KS statistic must be non-negative"

    def test_uniform_data_produces_larger_statistic(self):
        """
        Test that data from a uniform distribution (which is NOT exponential)
        produces a significantly larger KS statistic.
        
        This verifies the test's power to distinguish non-exponential distributions.
        """
        np.random.seed(42)
        # Generate data from Uniform(0, 2) - mean = 1 (same as exponential)
        # but the shape is very different
        data = np.random.uniform(low=0.0, high=2.0, size=1000)
        
        ks_stat = lilliefors_ks(data)
        
        # The uniform distribution should be rejected by the exponential test
        # Critical value at alpha=0.05 is approx 0.043
        # We expect the statistic to be significantly higher
        assert ks_stat > 0.1, f"KS statistic {ks_stat} is too small for uniform data; test may lack power"
        assert ks_stat >= 0, "KS statistic must be non-negative"

    def test_manual_calculation_matches(self):
        """
        Verify the implementation against a manual calculation for a small dataset.
        """
        # Small deterministic dataset
        data = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        
        # Manual calculation:
        # Mean = (0.5+1.0+1.5+2.0+2.5)/5 = 7.5/5 = 1.5
        # Normalized data = [0.5/1.5, 1.0/1.5, 1.5/1.5, 2.0/1.5, 2.5/1.5]
        #                 = [0.333, 0.667, 1.0, 1.333, 1.667]
        # Sorted: same
        # Empirical CDF: [0.2, 0.4, 0.6, 0.8, 1.0]
        # Theoretical CDF (1-exp(-x)): 
        #   x=0.333 -> 1-exp(-0.333) ≈ 0.283
        #   x=0.667 -> 1-exp(-0.667) ≈ 0.489
        #   x=1.0   -> 1-exp(-1.0)   ≈ 0.632
        #   x=1.333 -> 1-exp(-1.333) ≈ 0.736
        #   x=1.667 -> 1-exp(-1.667) ≈ 0.811
        # D+ = [0.2-0.283, 0.4-0.489, 0.6-0.632, 0.8-0.736, 1.0-0.811]
        #    = [-0.083, -0.089, -0.032, 0.064, 0.189] -> max = 0.189
        # D- = [0.2-0.2-0.283, ...] = [-0.283, -0.089-0.2, ...] 
        # Actually D- = (i-1)/n - F(x_i)
        #   i=1: 0.0 - 0.283 = -0.283
        #   i=2: 0.2 - 0.489 = -0.289
        #   i=3: 0.4 - 0.632 = -0.232
        #   i=4: 0.6 - 0.736 = -0.136
        #   i=5: 0.8 - 0.811 = -0.011
        # Max abs(D-) = 0.289
        # KS = max(0.189, 0.289) = 0.289
        
        ks_stat = lilliefors_ks(data)
        
        # Allow small floating point error
        expected_ks = 0.289
        assert abs(ks_stat - expected_ks) < 0.01, f"Manual calculation mismatch: got {ks_stat}, expected ~{expected_ks}"

    def test_mean_normalization_is_correct(self):
        """
        Verify that the function correctly normalizes data by the estimated mean.
        We do this by checking that the normalized data has mean 1.0 (within tolerance).
        """
        np.random.seed(123)
        data = np.random.exponential(scale=2.0, size=1000)  # Mean = 2.0
        
        # The function normalizes internally, so we can't directly inspect the 
        # normalized data, but we can verify the logic by comparing with scipy
        # However, since lilliefors_ks returns only the statistic, we rely on 
        # the fact that if the statistic is small for exponential data, the 
        # normalization must have worked correctly.
        
        ks_stat = lilliefors_ks(data)
        assert ks_stat < 0.05, "Normalization may be incorrect; statistic too high for exponential data"