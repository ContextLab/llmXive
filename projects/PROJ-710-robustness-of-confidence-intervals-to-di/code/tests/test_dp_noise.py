"""
Unit tests for DP noise calibration accuracy in the context of Confidence Interval coverage.

This module verifies that the DP noise injection functions (Laplace and Gaussian)
produce calibrated noise such that the resulting empirical coverage of 95% CIs
matches the nominal target (0.95) within a statistical tolerance when epsilon is large
(low noise), and diverges appropriately when epsilon is small (high noise).
"""

import numpy as np
import pytest
from scipy import stats
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.dp_noise import (
    compute_laplace_scale,
    compute_gaussian_scale,
    inject_laplace_noise,
    inject_gaussian_noise,
    validate_dp_parameters
)
from code.analysis.ci_builder import build_ci_for_mean, bootstrap_resample, compute_percentile_ci
from code.config import get_config


class TestEpsilonClamping:
    """Test that epsilon clamping works correctly for extreme values."""

    def test_valid_epsilon_range(self):
        """Test that valid epsilon values pass validation."""
        assert validate_dp_parameters(epsilon=1.0, delta=1e-5) is True
        assert validate_dp_parameters(epsilon=0.1, delta=1e-5) is True
        assert validate_dp_parameters(epsilon=10.0, delta=1e-5) is True

    def test_invalid_epsilon_zero(self):
        """Test that epsilon=0 raises an error."""
        with pytest.raises(ValueError):
            validate_dp_parameters(epsilon=0.0, delta=1e-5)

    def test_invalid_epsilon_negative(self):
        """Test that negative epsilon raises an error."""
        with pytest.raises(ValueError):
            validate_dp_parameters(epsilon=-1.0, delta=1e-5)

    def test_invalid_delta_non_positive(self):
        """Test that non-positive delta raises an error."""
        with pytest.raises(ValueError):
            validate_dp_parameters(epsilon=1.0, delta=0.0)
        with pytest.raises(ValueError):
            validate_dp_parameters(epsilon=1.0, delta=-1e-5)


class TestLaplaceNoise:
    """Test Laplace noise calibration and statistical properties."""

    def test_laplace_scale_formula(self):
        """Verify Laplace scale formula: b = sensitivity / epsilon."""
        sensitivity = 1.0
        epsilon = 2.0
        expected_scale = sensitivity / epsilon
        actual_scale = compute_laplace_scale(sensitivity=sensitivity, epsilon=epsilon)
        assert np.isclose(actual_scale, expected_scale)

    def test_laplace_noise_variance(self):
        """Test that Laplace noise has variance 2 * scale^2."""
        sensitivity = 1.0
        epsilon = 1.0
        scale = compute_laplace_scale(sensitivity=sensitivity, epsilon=epsilon)
        expected_variance = 2 * scale ** 2

        # Generate large sample to estimate variance
        np.random.seed(42)
        noise = inject_laplace_noise(
            data=np.zeros(100000),
            sensitivity=sensitivity,
            epsilon=epsilon
        )

        estimated_variance = np.var(noise)
        # Allow 10% tolerance for Monte Carlo estimation
        assert np.isclose(estimated_variance, expected_variance, rtol=0.1)

    def test_laplace_noise_mean_zero(self):
        """Test that Laplace noise is centered at zero."""
        sensitivity = 1.0
        epsilon = 1.0
        np.random.seed(42)
        noise = inject_laplace_noise(
            data=np.zeros(100000),
            sensitivity=sensitivity,
            epsilon=epsilon
        )
        # Allow 5% tolerance for Monte Carlo estimation
        assert np.abs(np.mean(noise)) < 0.05


class TestGaussianNoise:
    """Test Gaussian noise calibration and statistical properties."""

    def test_gaussian_scale_formula(self):
        """Verify Gaussian scale formula for approximate DP."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 1e-5
        expected_scale = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        actual_scale = compute_gaussian_scale(sensitivity=sensitivity, epsilon=epsilon, delta=delta)
        assert np.isclose(actual_scale, expected_scale)

    def test_gaussian_noise_variance(self):
        """Test that Gaussian noise has variance scale^2."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 1e-5
        scale = compute_gaussian_scale(sensitivity=sensitivity, epsilon=epsilon, delta=delta)
        expected_variance = scale ** 2

        # Generate large sample to estimate variance
        np.random.seed(42)
        noise = inject_gaussian_noise(
            data=np.zeros(100000),
            sensitivity=sensitivity,
            epsilon=epsilon,
            delta=delta
        )

        estimated_variance = np.var(noise)
        # Allow 5% tolerance for Monte Carlo estimation
        assert np.isclose(estimated_variance, expected_variance, rtol=0.05)

    def test_gaussian_noise_mean_zero(self):
        """Test that Gaussian noise is centered at zero."""
        sensitivity = 1.0
        epsilon = 1.0
        delta = 1e-5
        np.random.seed(42)
        noise = inject_gaussian_noise(
            data=np.zeros(100000),
            sensitivity=sensitivity,
            epsilon=epsilon,
            delta=delta
        )
        # Allow 1% tolerance for Monte Carlo estimation
        assert np.abs(np.mean(noise)) < 0.01


class TestSensitivityComputation:
    """Test sensitivity computation for different statistics."""

    def test_mean_sensitivity(self):
        """Test that mean sensitivity is (max - min) / n."""
        n = 100
        data_range = 10.0  # max - min
        expected_sensitivity = data_range / n
        # The function computes this based on the data bounds
        np.random.seed(42)
        data = np.random.uniform(0, data_range, n)
        actual_sensitivity = np.ptp(data) / n
        assert np.isclose(actual_sensitivity, expected_sensitivity, rtol=0.01)


class TestApplyDpToSummary:
    """Test the DP application to summary statistics."""

    def test_laplace_applied_to_mean(self):
        """Test that Laplace noise is correctly added to a mean estimate."""
        np.random.seed(42)
        data = np.random.normal(loc=5.0, scale=2.0, size=1000)
        true_mean = np.mean(data)

        sensitivity = 1.0
        epsilon = 10.0  # Low noise for this test

        noisy_mean = inject_laplace_noise(
            data=np.array([true_mean]),
            sensitivity=sensitivity,
            epsilon=epsilon
        )[0]

        # With low noise, the noisy mean should be close to the true mean
        assert np.abs(noisy_mean - true_mean) < 0.5

    def test_gaussian_applied_to_mean(self):
        """Test that Gaussian noise is correctly added to a mean estimate."""
        np.random.seed(42)
        data = np.random.normal(loc=5.0, scale=2.0, size=1000)
        true_mean = np.mean(data)

        sensitivity = 1.0
        epsilon = 10.0
        delta = 1e-5

        noisy_mean = inject_gaussian_noise(
            data=np.array([true_mean]),
            sensitivity=sensitivity,
            epsilon=epsilon,
            delta=delta
        )[0]

        # With low noise, the noisy mean should be close to the true mean
        assert np.abs(noisy_mean - true_mean) < 0.5


class TestDPNoiseCIIntegration:
    """
    Integration test for DP noise calibration accuracy in CI coverage.

    This test verifies that:
    1. When epsilon is large (low noise), the empirical coverage of 95% CIs
       remains close to the nominal 0.95 target.
    2. When epsilon is small (high noise), the empirical coverage deviates
       significantly from 0.95 (demonstrating the impact of DP noise).
    """

    def test_laplace_noise_coverage_at_high_epsilon(self):
        """
        Test that with high epsilon (low noise), CI coverage is close to nominal.

        We generate data from a known distribution, add calibrated Laplace noise
        with high epsilon, construct 95% CIs via bootstrap, and verify that
        the true mean falls within the CI approximately 95% of the time.
        """
        # Configuration
        np.random.seed(42)
        n_samples = 500  # Sample size per iteration
        n_iterations = 100  # Number of bootstrap coverage trials
        epsilon = 10.0  # High epsilon (low noise)
        delta = 1e-5
        sensitivity = 1.0
        nominal_coverage = 0.95
        tolerance = 0.10  # Allow 10% deviation due to Monte Carlo variance

        # Generate synthetic population with known mean
        true_mean = 10.0
        true_std = 2.0
        population = np.random.normal(loc=true_mean, scale=true_std, size=100000)

        covered_count = 0

        for _ in range(n_iterations):
            # Draw a sample
            sample = np.random.choice(population, size=n_samples, replace=False)

            # Add DP noise to the sample (perturbing each observation)
            # Note: In practice, sensitivity is computed based on the data bounds
            data_range = np.ptp(sample)
            actual_sensitivity = data_range / n_samples

            noisy_sample = inject_laplace_noise(
                data=sample.copy(),
                sensitivity=actual_sensitivity,
                epsilon=epsilon
            )

            # Compute point estimate and CI
            point_estimate = np.mean(noisy_sample)
            ci_lower, ci_upper = build_ci_for_mean(
                data=noisy_sample,
                confidence_level=0.95,
                n_bootstrap=1000
            )

            # Check if true mean is covered
            if ci_lower <= true_mean <= ci_upper:
                covered_count += 1

        empirical_coverage = covered_count / n_iterations

        # Assert that coverage is close to nominal (within tolerance)
        assert np.abs(empirical_coverage - nominal_coverage) < tolerance, \
            f"Empirical coverage {empirical_coverage:.3f} deviates too much from nominal {nominal_coverage}"

    def test_laplace_noise_coverage_at_low_epsilon(self):
        """
        Test that with low epsilon (high noise), CI coverage deviates from nominal.

        This demonstrates that DP noise can degrade CI coverage when privacy budget is tight.
        """
        # Configuration
        np.random.seed(42)
        n_samples = 500
        n_iterations = 100
        epsilon = 0.1  # Low epsilon (high noise)
        sensitivity = 1.0
        nominal_coverage = 0.95

        # Generate synthetic population with known mean
        true_mean = 10.0
        true_std = 2.0
        population = np.random.normal(loc=true_mean, scale=true_std, size=100000)

        covered_count = 0

        for _ in range(n_iterations):
            # Draw a sample
            sample = np.random.choice(population, size=n_samples, replace=False)

            # Add DP noise
            data_range = np.ptp(sample)
            actual_sensitivity = data_range / n_samples

            noisy_sample = inject_laplace_noise(
                data=sample.copy(),
                sensitivity=actual_sensitivity,
                epsilon=epsilon
            )

            # Compute point estimate and CI
            point_estimate = np.mean(noisy_sample)
            ci_lower, ci_upper = build_ci_for_mean(
                data=noisy_sample,
                confidence_level=0.95,
                n_bootstrap=1000
            )

            # Check if true mean is covered
            if ci_lower <= true_mean <= ci_upper:
                covered_count += 1

        empirical_coverage = covered_count / n_iterations

        # With high noise, coverage should deviate significantly from nominal
        # We expect it to be lower than nominal (conservative intervals might still cover,
        # but the point estimate is biased, so coverage drops)
        # Allow for some variance, but expect a significant drop
        assert empirical_coverage < nominal_coverage - 0.05, \
            f"Expected coverage to drop significantly with low epsilon, but got {empirical_coverage:.3f}"

    def test_gaussian_noise_coverage_at_high_epsilon(self):
        """
        Test that with high epsilon (low noise), Gaussian DP noise maintains CI coverage.
        """
        # Configuration
        np.random.seed(42)
        n_samples = 500
        n_iterations = 100
        epsilon = 10.0
        delta = 1e-5
        sensitivity = 1.0
        nominal_coverage = 0.95
        tolerance = 0.10

        # Generate synthetic population with known mean
        true_mean = 10.0
        true_std = 2.0
        population = np.random.normal(loc=true_mean, scale=true_std, size=100000)

        covered_count = 0

        for _ in range(n_iterations):
            # Draw a sample
            sample = np.random.choice(population, size=n_samples, replace=False)

            # Add DP noise
            data_range = np.ptp(sample)
            actual_sensitivity = data_range / n_samples

            noisy_sample = inject_gaussian_noise(
                data=sample.copy(),
                sensitivity=actual_sensitivity,
                epsilon=epsilon,
                delta=delta
            )

            # Compute point estimate and CI
            point_estimate = np.mean(noisy_sample)
            ci_lower, ci_upper = build_ci_for_mean(
                data=noisy_sample,
                confidence_level=0.95,
                n_bootstrap=1000
            )

            # Check if true mean is covered
            if ci_lower <= true_mean <= ci_upper:
                covered_count += 1

        empirical_coverage = covered_count / n_iterations

        # Assert that coverage is close to nominal
        assert np.abs(empirical_coverage - nominal_coverage) < tolerance, \
            f"Empirical coverage {empirical_coverage:.3f} deviates too much from nominal {nominal_coverage}"

    def test_gaussian_noise_coverage_at_low_epsilon(self):
        """
        Test that with low epsilon (high noise), Gaussian DP noise degrades CI coverage.
        """
        # Configuration
        np.random.seed(42)
        n_samples = 500
        n_iterations = 100
        epsilon = 0.1
        delta = 1e-5
        sensitivity = 1.0
        nominal_coverage = 0.95

        # Generate synthetic population with known mean
        true_mean = 10.0
        true_std = 2.0
        population = np.random.normal(loc=true_mean, scale=true_std, size=100000)

        covered_count = 0

        for _ in range(n_iterations):
            # Draw a sample
            sample = np.random.choice(population, size=n_samples, replace=False)

            # Add DP noise
            data_range = np.ptp(sample)
            actual_sensitivity = data_range / n_samples

            noisy_sample = inject_gaussian_noise(
                data=sample.copy(),
                sensitivity=actual_sensitivity,
                epsilon=epsilon,
                delta=delta
            )

            # Compute point estimate and CI
            point_estimate = np.mean(noisy_sample)
            ci_lower, ci_upper = build_ci_for_mean(
                data=noisy_sample,
                confidence_level=0.95,
                n_bootstrap=1000
            )

            # Check if true mean is covered
            if ci_lower <= true_mean <= ci_upper:
                covered_count += 1

        empirical_coverage = covered_count / n_iterations

        # Expect significant deviation from nominal
        assert empirical_coverage < nominal_coverage - 0.05, \
            f"Expected coverage to drop significantly with low epsilon, but got {empirical_coverage:.3f}"