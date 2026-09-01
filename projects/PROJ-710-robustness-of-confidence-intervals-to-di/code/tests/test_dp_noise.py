"""
Unit tests for DP noise calibration accuracy.
Tests inject_laplace_noise and inject_gaussian_noise from code/data/dp_noise.py.
Verifies that the empirical mean and variance of the injected noise match theoretical expectations.
"""
import numpy as np
import pytest
from scipy import stats
from pathlib import Path
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.dp_noise import inject_laplace_noise, inject_gaussian_noise
from code.config import Config


class TestEpsilonClamping:
    """Tests for edge cases in epsilon handling (integration with edge_cases.py)."""

    def test_zero_epsilon_raises(self):
        """Test that zero epsilon raises an error for Laplace noise."""
        data = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            inject_laplace_noise(data, epsilon=0.0, sensitivity=1.0)

    def test_negative_epsilon_raises(self):
        """Test that negative epsilon raises an error."""
        data = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            inject_laplace_noise(data, epsilon=-1.0, sensitivity=1.0)


class TestLaplaceNoise:
    """Tests for Laplace noise injection accuracy."""

    @pytest.fixture
    def large_sample(self):
        """Generate a large sample for statistical testing."""
        np.random.seed(42)
        return np.random.normal(loc=100.0, scale=10.0, size=100000)

    def test_noise_mean_near_zero(self, large_sample):
        """
        The mean of the injected Laplace noise should be close to 0.
        We subtract the original data to isolate the noise.
        """
        epsilon = 1.0
        sensitivity = 1.0
        noise_scale = sensitivity / epsilon

        noisy_data = inject_laplace_noise(large_sample, epsilon=epsilon, sensitivity=sensitivity)
        injected_noise = noisy_data - large_sample

        # Theoretical mean is 0
        # With N=100k, SE of mean ~ scale / sqrt(N) ~ 1 / 316 ~ 0.003
        # We allow a generous margin (5 sigma)
        mean_noise = np.mean(injected_noise)
        assert abs(mean_noise) < 5 * (noise_scale / np.sqrt(len(large_sample))), \
            f"Laplace noise mean {mean_noise} too far from 0"

    def test_noise_variance_matches_theory(self, large_sample):
        """
        The variance of Laplace noise should be 2 * scale^2.
        scale = sensitivity / epsilon.
        """
        epsilon = 2.0
        sensitivity = 1.0
        noise_scale = sensitivity / epsilon
        theoretical_variance = 2 * (noise_scale ** 2)

        noisy_data = inject_laplace_noise(large_sample, epsilon=epsilon, sensitivity=sensitivity)
        injected_noise = noisy_data - large_sample

        empirical_variance = np.var(injected_noise)

        # Allow 10% tolerance for sampling variance
        tolerance = 0.10 * theoretical_variance
        assert abs(empirical_variance - theoretical_variance) < tolerance, \
            f"Empirical variance {empirical_variance:.4f} differs from theoretical {theoretical_variance:.4f}"

    def test_noise_sensitivity_scaling(self):
        """
        Verify that doubling sensitivity doubles the noise scale (and thus variance).
        """
        np.random.seed(123)
        data = np.random.normal(0, 1, 50000)

        # Case 1: Sensitivity = 1
        noisy_1 = inject_laplace_noise(data, epsilon=1.0, sensitivity=1.0)
        noise_1 = noisy_1 - data
        var_1 = np.var(noise_1)

        # Case 2: Sensitivity = 2
        noisy_2 = inject_laplace_noise(data, epsilon=1.0, sensitivity=2.0)
        noise_2 = noisy_2 - data
        var_2 = np.var(noise_2)

        # Variance should be 4x (since scale is 2x, variance is 2*scale^2 -> 4x)
        # Allow 15% tolerance
        ratio = var_2 / var_1
        assert 3.0 < ratio < 5.0, f"Variance ratio {ratio} should be approx 4.0"


class TestGaussianNoise:
    """Tests for Gaussian noise injection accuracy."""

    @pytest.fixture
    def large_sample(self):
        np.random.seed(99)
        return np.random.normal(loc=50.0, scale=5.0, size=100000)

    def test_gaussian_noise_mean_near_zero(self, large_sample):
        """
        The mean of injected Gaussian noise should be close to 0.
        """
        epsilon = 1.0
        sensitivity = 1.0
        # For Gaussian, we typically use a delta parameter, but our function
        # likely derives sigma from epsilon and a fixed delta or uses a standard formula.
        # We check that the mean is near zero regardless of the exact sigma derivation.
        
        noisy_data = inject_gaussian_noise(large_sample, epsilon=epsilon, sensitivity=sensitivity)
        injected_noise = noisy_data - large_sample

        mean_noise = np.mean(injected_noise)
        # Allow 5 sigma margin
        std_error = np.std(injected_noise) / np.sqrt(len(large_sample))
        assert abs(mean_noise) < 5 * std_error, \
            f"Gaussian noise mean {mean_noise} too far from 0"

    def test_gaussian_noise_variance_scaling(self):
        """
        Verify that increasing epsilon reduces noise variance (inverse relationship).
        """
        np.random.seed(456)
        data = np.random.normal(0, 1, 50000)

        # Low epsilon -> High noise
        noisy_low = inject_gaussian_noise(data, epsilon=0.5, sensitivity=1.0)
        noise_low = noisy_low - data
        var_low = np.var(noise_low)

        # High epsilon -> Low noise
        noisy_high = inject_gaussian_noise(data, epsilon=5.0, sensitivity=1.0)
        noise_high = noisy_high - data
        var_high = np.var(noise_high)

        # Variance should be significantly smaller for higher epsilon
        assert var_high < var_low, "Higher epsilon should result in lower noise variance"
        assert var_low / var_high > 1.5, "Variance reduction should be substantial"


class TestSensitivityComputation:
    """Tests related to sensitivity parameter handling."""

    def test_sensitivity_zero_raises(self):
        """Sensitivity of 0 should raise an error (division by zero)."""
        data = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            inject_laplace_noise(data, epsilon=1.0, sensitivity=0.0)

        with pytest.raises(ValueError):
            inject_gaussian_noise(data, epsilon=1.0, sensitivity=0.0)


class TestApplyDpToSummary:
    """Tests for applying DP noise to summary statistics (indirectly)."""
    
    def test_noise_preserves_data_shape(self):
        """Injected noise should not change the shape of the data."""
        np.random.seed(789)
        data = np.random.normal(0, 1, (100, 5))
        
        noisy_lap = inject_laplace_noise(data, epsilon=1.0, sensitivity=1.0)
        noisy_gauss = inject_gaussian_noise(data, epsilon=1.0, sensitivity=1.0)
        
        assert noisy_lap.shape == data.shape
        assert noisy_gauss.shape == data.shape


class TestDPNoiseCIIntegration:
    """Integration test: Verify that noisy data affects CI coverage as expected."""
    
    def test_noisy_data_wider_ci(self):
        """
        Injecting noise should increase the variance of the data,
        leading to wider confidence intervals compared to clean data.
        """
        np.random.seed(101)
        clean_data = np.random.normal(loc=10.0, scale=2.0, size=1000)
        
        # Clean CI (approx)
        clean_mean = np.mean(clean_data)
        clean_se = np.std(clean_data, ddof=1) / np.sqrt(len(clean_data))
        clean_ci_width = 2 * 1.96 * clean_se  # 95% CI approx
        
        # Noisy data
        noisy_data = inject_laplace_noise(clean_data, epsilon=0.5, sensitivity=1.0)
        noisy_mean = np.mean(noisy_data)
        noisy_se = np.std(noisy_data, ddof=1) / np.sqrt(len(noisy_data))
        noisy_ci_width = 2 * 1.96 * noisy_se
        
        # Noisy CI should be wider due to added variance
        assert noisy_ci_width > clean_ci_width, \
            f"Noisy CI width {noisy_ci_width:.4f} should be > Clean CI width {clean_ci_width:.4f}"