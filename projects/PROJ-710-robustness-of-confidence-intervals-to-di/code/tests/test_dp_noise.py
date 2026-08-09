"""
Unit tests for DP noise injection module.

Tests cover:
- Laplace noise calibration
- Gaussian noise calibration
- Sensitivity computation
- Parameter validation
- End-to-end DP application
"""

import numpy as np
import pytest
from scipy import stats
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.dp_noise import (
    compute_laplace_scale,
    compute_gaussian_scale,
    add_laplace_noise,
    add_gaussian_noise,
    compute_mean_sensitivity,
    compute_sum_sensitivity,
    apply_dp_noise,
    apply_dp_to_summary,
    validate_dp_parameters,
    dp_mean,
    dp_sum
)


class TestEpsilonClamping:
    """Test epsilon parameter validation and clamping behavior."""

    def test_epsilon_positive_required(self):
        """Epsilon must be positive for both mechanisms."""
        with pytest.raises(ValueError):
            compute_laplace_scale(sensitivity=1.0, epsilon=0)

        with pytest.raises(ValueError):
            compute_laplace_scale(sensitivity=1.0, epsilon=-1.0)

    def test_gaussian_delta_positive_required(self):
        """Delta must be positive for Gaussian mechanism."""
        with pytest.raises(ValueError):
            compute_gaussian_scale(sensitivity=1.0, epsilon=1.0, delta=0)

        with pytest.raises(ValueError):
            compute_gaussian_scale(sensitivity=1.0, epsilon=1.0, delta=-0.01)

    def test_sensitivity_non_negative(self):
        """Sensitivity must be non-negative."""
        with pytest.raises(ValueError):
            compute_laplace_scale(sensitivity=-1.0, epsilon=1.0)


class TestLaplaceNoise:
    """Test Laplace noise generation and properties."""

    def test_laplace_scale_formula(self):
        """Verify Laplace scale: b = sensitivity / epsilon."""
        sensitivity = 2.0
        epsilon = 0.5
        expected_scale = 4.0

        assert compute_laplace_scale(sensitivity, epsilon) == expected_scale

    def test_laplace_noise_zero_mean(self):
        """Laplace noise should have mean close to zero for large samples."""
        np.random.seed(42)
        n_samples = 100000
        scale = 1.0

        noise = np.random.laplace(loc=0.0, scale=scale, size=n_samples)

        # Mean should be close to 0 (within 3 standard errors)
        se = scale / np.sqrt(n_samples)
        assert abs(np.mean(noise)) < 3 * se

    def test_laplace_noise_variance(self):
        """Laplace noise variance should be 2 * scale^2."""
        np.random.seed(42)
        n_samples = 100000
        scale = 2.0

        noise = np.random.laplace(loc=0.0, scale=scale, size=n_samples)

        # Variance of Laplace is 2 * b^2
        expected_var = 2 * scale**2
        actual_var = np.var(noise)

        # Allow 10% tolerance for sampling variation
        assert abs(actual_var - expected_var) / expected_var < 0.1

    def test_add_laplace_noise_preserves_shape(self):
        """Adding Laplace noise should preserve input shape."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        noisy = add_laplace_noise(data, scale=0.1, random_state=42)

        assert noisy.shape == data.shape
        assert noisy.dtype == np.float64

    def test_add_laplace_noise_deterministic(self):
        """Same random_state should produce same results."""
        data = np.array([1.0, 2.0, 3.0])

        noisy1 = add_laplace_noise(data, scale=0.5, random_state=123)
        noisy2 = add_laplace_noise(data, scale=0.5, random_state=123)

        np.testing.assert_array_equal(noisy1, noisy2)


class TestGaussianNoise:
    """Test Gaussian noise generation and properties."""

    def test_gaussian_scale_basic(self):
        """Verify Gaussian scale formula (basic mechanism)."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 0.01

        scale = compute_gaussian_scale(sensitivity, epsilon, delta, mechanism="basic")

        # sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        expected = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        assert abs(scale - expected) < 1e-10

    def test_gaussian_scale_advanced(self):
        """Verify Gaussian scale formula (advanced mechanism)."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 0.01

        scale = compute_gaussian_scale(sensitivity, epsilon, delta, mechanism="advanced")

        # sigma = sensitivity * sqrt(2 * ln(1/delta)) / epsilon
        expected = sensitivity * np.sqrt(2 * np.log(1 / delta)) / epsilon
        assert abs(scale - expected) < 1e-10

    def test_gaussian_noise_zero_mean(self):
        """Gaussian noise should have mean close to zero for large samples."""
        np.random.seed(42)
        n_samples = 100000
        scale = 1.0

        noise = np.random.normal(loc=0.0, scale=scale, size=n_samples)

        # Mean should be close to 0 (within 3 standard errors)
        se = scale / np.sqrt(n_samples)
        assert abs(np.mean(noise)) < 3 * se

    def test_gaussian_noise_variance(self):
        """Gaussian noise variance should be scale^2."""
        np.random.seed(42)
        n_samples = 100000
        scale = 2.0

        noise = np.random.normal(loc=0.0, scale=scale, size=n_samples)

        expected_var = scale**2
        actual_var = np.var(noise)

        # Allow 5% tolerance for sampling variation
        assert abs(actual_var - expected_var) / expected_var < 0.05

    def test_add_gaussian_noise_preserves_shape(self):
        """Adding Gaussian noise should preserve input shape."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        noisy = add_gaussian_noise(data, scale=0.1, random_state=42)

        assert noisy.shape == data.shape
        assert noisy.dtype == np.float64

    def test_add_gaussian_noise_deterministic(self):
        """Same random_state should produce same results."""
        data = np.array([1.0, 2.0, 3.0])

        noisy1 = add_gaussian_noise(data, scale=0.5, random_state=123)
        noisy2 = add_gaussian_noise(data, scale=0.5, random_state=123)

        np.testing.assert_array_equal(noisy1, noisy2)


class TestSensitivityComputation:
    """Test sensitivity computation functions."""

    def test_mean_sensitivity_formula(self):
        """Verify mean sensitivity: range / n."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        n = len(data)

        sensitivity = compute_mean_sensitivity(data, n)
        expected = (5.0 - 1.0) / 5.0  # range / n

        assert abs(sensitivity - expected) < 1e-10

    def test_sum_sensitivity_formula(self):
        """Verify sum sensitivity: range."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        sensitivity = compute_sum_sensitivity(data)
        expected = 5.0 - 1.0  # range

        assert abs(sensitivity - expected) < 1e-10

    def test_mean_sensitivity_empty(self):
        """Mean sensitivity should fail for n=0."""
        data = np.array([])
        with pytest.raises(ValueError):
            compute_mean_sensitivity(data, 0)


class TestApplyDpToSummary:
    """Test applying DP noise to summary statistics."""

    def test_dp_mean_basic(self):
        """Test DP mean with known sensitivity."""
        np.random.seed(42)
        data = np.random.normal(loc=10.0, scale=2.0, size=1000)

        true_mean = np.mean(data)
        sensitivity = compute_mean_sensitivity(data, len(data))

        noisy_mean, metadata = apply_dp_to_summary(
            true_mean, sensitivity, epsilon=1.0, noise_type="laplace", random_state=42
        )

        # Noisy mean should be different from true mean
        assert abs(noisy_mean - true_mean) > 0.001

        # Metadata should contain expected fields
        assert "scale" in metadata
        assert "epsilon" in metadata
        assert "noise_type" in metadata
        assert metadata["epsilon"] == 1.0
        assert metadata["noise_type"] == "laplace"

    def test_dp_mean_gaussian(self):
        """Test DP mean with Gaussian noise."""
        np.random.seed(42)
        data = np.random.normal(loc=10.0, scale=2.0, size=1000)

        true_mean = np.mean(data)
        sensitivity = compute_mean_sensitivity(data, len(data))

        noisy_mean, metadata = apply_dp_to_summary(
            true_mean, sensitivity, epsilon=1.0, noise_type="gaussian", delta=0.0001, random_state=42
        )

        assert abs(noisy_mean - true_mean) > 0.001
        assert metadata["noise_type"] == "gaussian"

    def test_dp_sum(self):
        """Test DP sum computation."""
        np.random.seed(42)
        data = np.random.normal(loc=10.0, scale=2.0, size=100)

        true_sum = np.sum(data)
        sensitivity = compute_sum_sensitivity(data)

        noisy_sum, metadata = dp_sum(data, epsilon=1.0, random_state=42)

        # Noisy sum should be different from true sum
        assert abs(noisy_sum - true_sum) > 0.001


class TestDPNoiseCIIntegration:
    """Integration tests for DP noise in CI context."""

    def test_apply_dp_noise_array(self):
        """Test applying DP noise to an entire array."""
        np.random.seed(42)
        data = np.random.normal(loc=10.0, scale=2.0, size=100)

        noisy_data, metadata = apply_dp_noise(
            data, epsilon=1.0, noise_type="laplace", random_state=42
        )

        assert noisy_data.shape == data.shape
        assert metadata["epsilon"] == 1.0
        assert metadata["noise_type"] == "laplace"

    def test_apply_dp_noise_validation(self):
        """Test parameter validation in apply_dp_noise."""
        data = np.array([1.0, 2.0, 3.0])

        # Invalid epsilon
        with pytest.raises(ValueError):
            apply_dp_noise(data, epsilon=0, noise_type="laplace")

        # Invalid noise_type
        with pytest.raises(ValueError):
            apply_dp_noise(data, epsilon=1.0, noise_type="invalid")

        # Gaussian without delta
        with pytest.raises(ValueError):
            apply_dp_noise(data, epsilon=1.0, noise_type="gaussian", delta=None)

    def test_validate_dp_parameters(self):
        """Test DP parameter validation."""
        config = validate_dp_parameters(epsilon=1.0, noise_type="laplace")

        assert config["mechanism"] == "epsilon-DP (Laplace)"
        assert config["epsilon"] == 1.0
        assert config["delta"] == 0.0

        config_gaussian = validate_dp_parameters(
            epsilon=1.0, delta=0.0001, noise_type="gaussian"
        )

        assert config_gaussian["mechanism"] == "(epsilon, delta)-DP (Gaussian)"
        assert config_gaussian["epsilon"] == 1.0
        assert config_gaussian["delta"] == 0.0001

    def test_laplace_vs_gaussian_noise_scale(self):
        """Compare noise scales for same epsilon."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 0.0001

        laplace_scale = compute_laplace_scale(sensitivity, epsilon)
        gaussian_scale = compute_gaussian_scale(sensitivity, epsilon, delta)

        # Gaussian typically requires larger scale for same epsilon
        # (due to the delta term)
        assert gaussian_scale > laplace_scale
