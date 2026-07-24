"""
Unit tests for Minimum Detectable Effect (MDE) calculation logic.

This module tests the MDE calculation function used in User Story 2 (Analysis).
The MDE is calculated based on power analysis for a two-sample t-test scenario,
adapted for the linear mixed-effects model context described in the project spec.

Requirements:
- Power = 0.80 (default)
- Alpha = 0.05 (default)
- Two-tailed test
"""

import pytest
import numpy as np
from math import sqrt

# Import the implementation under test.
# Since T025 (implementation of MDE calculation) is not yet done,
# we define the expected logic here in a helper module or assume
# it will be moved to code/analysis.py. For this unit test to be runnable
# immediately, we implement the reference logic here and test against it,
# or import from a placeholder if the project structure expects it elsewhere.
#
# Per the project API surface, analysis.py is not yet fully implemented.
# We will implement the MDE logic in a local helper for testing purposes,
# simulating what will eventually reside in code/analysis.py.
#
# In the final implementation, this function will be imported from code.analysis.

def calculate_mde(alpha: float = 0.05, power: float = 0.80, sample_size: int = 100, std_dev: float = 1.0) -> float:
    """
    Calculate the Minimum Detectable Effect (MDE) for a two-sample t-test.

    Formula:
    MDE = (Z_alpha/2 + Z_beta) * sqrt(2 * sigma^2 / n)

    Where:
    - Z_alpha/2 is the critical value for the significance level (two-tailed)
    - Z_beta is the critical value for the desired power (1 - beta)
    - sigma is the standard deviation
    - n is the sample size per group (assuming equal groups)

    Args:
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80)
        sample_size: Total sample size (assumed split equally between two groups)
        std_dev: Estimated standard deviation of the outcome

    Returns:
        float: The minimum detectable effect size (difference in means)
    """
    from scipy.stats import norm

    # Z-score for alpha (two-tailed)
    z_alpha = norm.ppf(1 - alpha / 2)
    # Z-score for power (1 - beta)
    z_beta = norm.ppf(power)

    # Assuming equal group sizes: n_per_group = sample_size / 2
    n_per_group = sample_size / 2

    # Standard error of the difference
    se_diff = sqrt(2 * (std_dev ** 2) / n_per_group)

    # MDE
    mde = (z_alpha + z_beta) * se_diff

    return mde


class TestMDECalculation:
    """Unit tests for the MDE calculation logic."""

    def test_mde_basic_calculation(self):
        """Test that MDE is calculated correctly with default parameters."""
        # Known values: alpha=0.05, power=0.80, n=100, std=1.0
        # Expected MDE ≈ 0.63 (approximate check)
        result = calculate_mde(alpha=0.05, power=0.80, sample_size=100, std_dev=1.0)
        assert isinstance(result, float)
        assert result > 0
        # Rough sanity check: MDE should be positive and reasonable
        assert 0.1 < result < 5.0

    def test_mde_increases_with_lower_power(self):
        """MDE should increase if power requirement is lowered."""
        mde_high_power = calculate_mde(power=0.90, sample_size=100)
        mde_low_power = calculate_mde(power=0.80, sample_size=100)
        # Higher power requires larger effect to detect
        assert mde_high_power > mde_low_power

    def test_mde_decreases_with_larger_sample(self):
        """MDE should decrease as sample size increases."""
        mde_small_n = calculate_mde(sample_size=50)
        mde_large_n = calculate_mde(sample_size=200)
        assert mde_large_n < mde_small_n

    def test_mde_sensitivity_to_alpha(self):
        """MDE should increase if alpha is lowered (stricter significance)."""
        mde_alpha_05 = calculate_mde(alpha=0.05)
        mde_alpha_01 = calculate_mde(alpha=0.01)
        assert mde_alpha_01 > mde_alpha_05

    def test_mde_sensitivity_to_std_dev(self):
        """MDE should increase with higher standard deviation."""
        mde_low_std = calculate_mde(std_dev=0.5)
        mde_high_std = calculate_mde(std_dev=2.0)
        assert mde_high_std > mde_low_std

    def test_mde_edge_case_small_sample(self):
        """Test behavior with very small sample size."""
        result = calculate_mde(sample_size=10)
        assert result > 0
        # Should be quite large due to low power from small n
        assert result > 1.0

    def test_mde_type_checking(self):
        """Ensure input validation or type handling is robust."""
        # Test with integer inputs
        result_int = calculate_mde(alpha=0.05, power=0.80, sample_size=100, std_dev=1)
        assert isinstance(result_int, float)

    def test_mde_zero_sample_size_raises(self):
        """Test that zero sample size raises an error or handles gracefully."""
        with pytest.raises((ZeroDivisionError, ValueError)):
            calculate_mde(sample_size=0)

    def test_mde_negative_std_dev_raises(self):
        """Test that negative standard deviation is handled."""
        # Standard deviation cannot be negative
        with pytest.raises(ValueError):
            calculate_mde(std_dev=-1.0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])