"""
Unit tests for the data_generator module.
Implements TDD tests for User Story 1.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_generator import (
    generate_normal,
    generate_uniform,
    generate_log_normal,
    generate_data,
    validate_sample_statistics
)
from code.config import SEED_BASE

class TestNormalMeanValidation:
    """T009a: Verify sample mean difference for normal distribution is within tolerance."""

    def test_normal_mean_validation(self):
        """
        Verify sample mean difference for normal distribution (n=50, effect=0.0)
        is within 1e-6 of 0.0.
        """
        n = 50
        effect = 0.0
        seed = SEED_BASE + 1001  # Unique seed for this test

        group1, group2 = generate_normal(n, effect, seed=seed)

        mean_diff = np.mean(group2) - np.mean(group1)

        # Assert the mean difference is within the strict tolerance
        assert abs(mean_diff) < 1e-6, f"Mean diff {mean_diff} exceeds tolerance 1e-6"

class TestLognormalSkewnessValidation:
    """T009b: Verify skewness of log-normal distribution matches theoretical value."""

    def test_lognormal_skewness_validation(self):
        """
        Verify skewness of log-normal distribution (n=30) matches the theoretical value
        (exp(sigma^2) + 2) * sqrt(exp(sigma^2) - 1) within the theoretical standard error
        of skewness for n=30 (approx 0.42).
        """
        n = 30
        effect = 0.0  # Null hypothesis, but distribution shape is what matters
        sigma = 0.5  # Standard parameter for log-normal in generator
        seed = SEED_BASE + 1002

        # Generate data
        group1, _ = generate_log_normal(n, effect, sigma=sigma, seed=seed)

        # Calculate sample skewness
        sample_skewness = stats.skew(group1)

        # Calculate theoretical skewness for LogNormal(0, sigma^2)
        # Formula: (exp(sigma^2) + 2) * sqrt(exp(sigma^2) - 1)
        theoretical_skewness = (np.exp(sigma**2) + 2) * np.sqrt(np.exp(sigma**2) - 1)

        # Theoretical standard error of skewness for n=30 is approx sqrt(6/n)
        # For n=30, SE ~ sqrt(0.2) ~ 0.447. We use a slightly tighter bound for safety.
        se_skewness = np.sqrt(6 / n)

        tolerance = 3 * se_skewness  # 3 standard errors

        assert abs(sample_skewness - theoretical_skewness) < tolerance, \
            f"Sample skewness {sample_skewness:.4f} differs from theoretical {theoretical_skewness:.4f} by more than {tolerance:.4f}"

class TestLognormalEffectSizeValidation:
    """T009c: Verify mean difference for log-normal distribution matches effect size."""

    def test_lognormal_effect_size_validation(self):
        """
        Verify mean difference for log-normal distribution (n=30, effect=0.5)
        is within 1e-6 of 0.5.
        """
        n = 30
        effect = 0.5
        sigma = 0.5
        seed = SEED_BASE + 1003

        group1, group2 = generate_log_normal(n, effect, sigma=sigma, seed=seed)

        mean_diff = np.mean(group2) - np.mean(group1)

        # Assert the mean difference is within the strict tolerance
        assert abs(mean_diff - effect) < 1e-6, \
            f"Mean diff {mean_diff} differs from expected effect {effect} by more than 1e-6"

class TestUniformSampleSizeAccuracy:
    """T009d: Verify sample size for uniform distribution is exactly as requested."""

    def test_uniform_sample_size_accuracy(self):
        """
        Verify sample size for uniform distribution (n=1000) is exactly 1000
        and data fits uniform profile.
        """
        n = 1000
        effect = 0.0
        seed = SEED_BASE + 1004

        group1, group2 = generate_uniform(n, effect, seed=seed)

        # 1. Verify exact sample size
        assert len(group1) == n, f"Expected sample size {n}, got {len(group1)}"
        assert len(group2) == n, f"Expected sample size {n}, got {len(group2)}"

        # 2. Verify data fits uniform profile
        # For Uniform(0, 1), mean should be ~0.5, variance ~1/12
        # We use a relaxed tolerance for sample statistics compared to theoretical
        # but strict enough to catch gross errors.
        
        mean1 = np.mean(group1)
        mean2 = np.mean(group2)
        
        # Expected mean for Uniform(0,1) is 0.5
        # Standard error of mean is sigma/sqrt(n) = (1/sqrt(12))/sqrt(1000) ~ 0.009
        # 3 SE tolerance ~ 0.027
        expected_mean = 0.5
        tolerance_mean = 0.05 
        
        assert abs(mean1 - expected_mean) < tolerance_mean, \
            f"Group 1 mean {mean1} outside expected range for uniform distribution"
        assert abs(mean2 - expected_mean) < tolerance_mean, \
            f"Group 2 mean {mean2} outside expected range for uniform distribution"

        # Verify variance is positive and reasonable (1/12 ~ 0.083)
        var1 = np.var(group1)
        var2 = np.var(group2)
        
        assert var1 > 0.01 and var1 < 0.2, f"Group 1 variance {var1} outside uniform range"
        assert var2 > 0.01 and var2 < 0.2, f"Group 2 variance {var2} outside uniform range"

        # 3. Verify effect size is respected (effect=0.0 means means should be equal)
        mean_diff = np.mean(group2) - np.mean(group1)
        # With n=1000, the standard error of the difference is small (~0.013)
        # We check that the difference is not significantly large relative to the distribution
        assert abs(mean_diff) < 0.1, f"Mean diff {mean_diff} too large for effect=0.0"

class TestGenerateDataInterface:
    """Tests for the generic generate_data function interface."""

    def test_generate_data_uniform_kwargs(self):
        """
        Verify generate_data accepts kwargs as used in run_data_gen.py:
        generate_data(sample_size=..., distribution_type='uniform', ...)
        """
        kwargs = {
            'sample_size': 100,
            'distribution_type': 'uniform',
            'effect_size': 0.0,
            'seed': SEED_BASE + 1005
        }
        
        # This should not raise TypeError
        group1, group2 = generate_data(**kwargs)
        
        assert len(group1) == 100
        assert len(group2) == 100

    def test_generate_data_normal_kwargs(self):
        """
        Verify generate_data accepts kwargs for normal distribution.
        """
        kwargs = {
            'sample_size': 50,
            'distribution_type': 'normal',
            'effect_size': 0.5,
            'seed': SEED_BASE + 1006
        }
        
        group1, group2 = generate_data(**kwargs)
        
        assert len(group1) == 50
        assert len(group2) == 50

    def test_generate_data_lognormal_kwargs(self):
        """
        Verify generate_data accepts kwargs for log-normal distribution.
        """
        kwargs = {
            'sample_size': 30,
            'distribution_type': 'log_normal',
            'effect_size': 0.5,
            'seed': SEED_BASE + 1007
        }
        
        group1, group2 = generate_data(**kwargs)
        
        assert len(group1) == 30
        assert len(group2) == 30

    def test_generate_data_positional_args(self):
        """
        Verify generate_data accepts positional args as used in run_ground_truth_validation.py:
        generate_data(n, dist, eff, seed=seed)
        """
        # Call with positional arguments
        group1, group2 = generate_data(100, 'uniform', 0.0, seed=SEED_BASE + 1008)
        
        assert len(group1) == 100
        assert len(group2) == 100

    def test_generate_data_effect_size_validation(self):
        """
        Verify that generate_data correctly applies effect sizes.
        """
        # Test with effect=0.5, normal distribution
        group1, group2 = generate_data(1000, 'normal', 0.5, seed=SEED_BASE + 1009)
        
        mean_diff = np.mean(group2) - np.mean(group1)
        # With large n, the observed difference should be close to the effect size
        assert abs(mean_diff - 0.5) < 0.1, f"Effect size {mean_diff} differs from 0.5"

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_distribution_type(self):
        """Verify generate_data raises error for unknown distribution type."""
        with pytest.raises(ValueError):
            generate_data(100, 'invalid_dist', 0.0, seed=42)

    def test_zero_sample_size(self):
        """Verify behavior with zero sample size (should return empty arrays)."""
        group1, group2 = generate_data(0, 'uniform', 0.0, seed=42)
        assert len(group1) == 0
        assert len(group2) == 0

    def test_negative_sample_size(self):
        """Verify behavior with negative sample size."""
        with pytest.raises(ValueError):
            generate_data(-1, 'uniform', 0.0, seed=42)

# Import stats inside the class to avoid top-level import issues if scipy not installed
from scipy import stats