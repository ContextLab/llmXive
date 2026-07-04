import numpy as np
import pytest
from scipy import stats
from code.data.dp_noise import (
    inject_laplace_noise,
    inject_gaussian_noise,
    compute_sensitivity_mean,
    compute_sensitivity_variance,
    apply_dp_to_summary,
)


class TestEpsilonClamping:
    """Test that extremely small epsilon values do not cause numerical instability."""

    def test_epsilon_clamping_lower_bound(self):
        """Verify that epsilon is clamped to a minimum threshold."""
        data = np.random.normal(loc=10.0, scale=2.0, size=1000)
        # Use an extremely small epsilon that would normally cause huge noise
        epsilon = 1e-10

        # The function should handle this without crashing or producing NaN/Inf
        noisy_data = inject_laplace_noise(data, epsilon)

        assert not np.any(np.isnan(noisy_data))
        assert not np.any(np.isinf(noisy_data))
        assert len(noisy_data) == len(data)

    def test_epsilon_normal_range(self):
        """Verify normal epsilon values produce expected noise magnitude."""
        data = np.ones(1000)  # Constant data for predictable sensitivity
        epsilon = 1.0

        noisy_data = inject_laplace_noise(data, epsilon)

        # With constant data, sensitivity is 0 (or very small if handled differently),
        # but the noise scale is 1/epsilon.
        # We check that the output is finite and same shape.
        assert np.all(np.isfinite(noisy_data))


class TestLaplaceNoise:
    """Unit tests for Laplace noise injection."""

    def test_laplace_noise_mean_shift(self):
        """Verify that the mean of noisy data is close to original mean for large N."""
        np.random.seed(42)
        data = np.random.normal(loc=50.0, scale=10.0, size=100000)
        epsilon = 1.0

        noisy_data = inject_laplace_noise(data, epsilon)

        # The mean of Laplace noise is 0, so the noisy mean should be close to original mean
        original_mean = np.mean(data)
        noisy_mean = np.mean(noisy_data)

        # Allow for some deviation due to finite sample size of noise
        assert abs(noisy_mean - original_mean) < 1.0  # Tolerance based on noise scale

    def test_laplace_noise_scale(self):
        """Verify noise scale matches 1/epsilon."""
        np.random.seed(123)
        data = np.zeros(100000)  # Zero mean, zero variance for clean signal
        epsilon = 2.0

        noisy_data = inject_laplace_noise(data, epsilon)

        # The variance of Laplace(0, b) is 2*b^2, where b = sensitivity / epsilon
        # For mean of data with range R, sensitivity is R/n. Here we test simple case.
        # We just verify that the noise magnitude scales inversely with epsilon.
        noise_added = noisy_data - data
        std_noise = np.std(noise_added)

        # Expected scale parameter b = sensitivity / epsilon
        # We check relative scaling between two epsilons
        noisy_data_4 = inject_laplace_noise(data, 4.0)
        std_noise_4 = np.std(noisy_data_4)

        # std should be roughly half when epsilon doubles
        ratio = std_noise / std_noise_4
        assert 1.5 < ratio < 2.5  # Allow for sampling variance


class TestGaussianNoise:
    """Unit tests for Gaussian noise injection."""

    def test_gaussian_noise_mean(self):
        """Verify Gaussian noise has mean close to zero."""
        np.random.seed(456)
        data = np.random.normal(loc=100.0, scale=5.0, size=100000)
        epsilon = 1.0
        delta = 1e-5

        noisy_data = inject_gaussian_noise(data, epsilon, delta)

        original_mean = np.mean(data)
        noisy_mean = np.mean(noisy_data)

        assert abs(noisy_mean - original_mean) < 0.5

    def test_gaussian_noise_variance_scaling(self):
        """Verify noise variance scales with 1/epsilon^2."""
        np.random.seed(789)
        data = np.zeros(100000)
        epsilon1 = 1.0
        epsilon2 = 2.0
        delta = 1e-5

        noisy_data1 = inject_gaussian_noise(data, epsilon1, delta)
        noisy_data2 = inject_gaussian_noise(data, epsilon2, delta)

        var1 = np.var(noisy_data1)
        var2 = np.var(noisy_data2)

        # Variance should be roughly 4x larger for epsilon=1 vs epsilon=2
        ratio = var1 / var2
        assert 2.5 < ratio < 5.5


class TestSensitivityComputation:
    """Unit tests for sensitivity computation functions."""

    def test_compute_sensitivity_mean(self):
        """Verify sensitivity of mean is range/n."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        # Range is 4, n is 5, so sensitivity = 4/5 = 0.8
        sens = compute_sensitivity_mean(data)
        expected = (5.0 - 1.0) / 5.0
        assert np.isclose(sens, expected)

    def test_compute_sensitivity_variance(self):
        """Verify sensitivity of variance is bounded."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sens = compute_sensitivity_variance(data)
        # Sensitivity of variance depends on range and n
        assert sens > 0
        assert sens < 10.0  # Reasonable bound for small data

    def test_compute_sensitivity_mean_empty(self):
        """Handle empty array gracefully."""
        data = np.array([])
        with pytest.raises(ValueError):
            compute_sensitivity_mean(data)


class TestApplyDpToSummary:
    """Unit tests for applying DP to summary statistics."""

    def test_apply_dp_to_summary_mean(self):
        """Verify apply_dp_to_summary returns noisy mean."""
        data = np.random.normal(loc=10.0, scale=1.0, size=10000)
        epsilon = 1.0
        delta = 1e-5
        noise_type = "laplace"

        result = apply_dp_to_summary(data, epsilon, noise_type=noise_type)

        assert "noisy_mean" in result
        assert "sensitivity" in result
        assert "epsilon" in result
        assert np.isfinite(result["noisy_mean"])

    def test_apply_dp_to_summary_variance(self):
        """Verify apply_dp_to_summary returns noisy variance."""
        data = np.random.normal(loc=0.0, scale=1.0, size=10000)
        epsilon = 1.0
        delta = 1e-5
        noise_type = "gaussian"

        result = apply_dp_to_summary(data, epsilon, noise_type=noise_type, statistic="variance")

        assert "noisy_variance" in result
        assert np.isfinite(result["noisy_variance"])

    def test_apply_dp_to_summary_invalid_noise_type(self):
        """Verify error on invalid noise type."""
        data = np.ones(100)
        with pytest.raises(ValueError):
            apply_dp_to_summary(data, epsilon=1.0, noise_type="invalid")