"""
Unit tests for power analysis calculations.
"""
import pytest
import numpy as np
from code.analysis.power_analysis import calculate_mdes, calculate_power

class TestPowerAnalysis:
    def test_mdes_calculation(self):
        """Test that MDES decreases as sample size increases."""
        mdes_20 = calculate_mdes(n=20)
        mdes_50 = calculate_mdes(n=50)
        mdes_100 = calculate_mdes(n=100)

        assert mdes_20 > mdes_50 > mdes_100, "MDES should decrease with larger N"
        # Check that MDES for n=50 is roughly in the expected range (~0.6-0.7 for alpha=0.05, power=0.8)
        # Approximation: 2.8 / sqrt(50) ≈ 0.4
        assert 0.4 < mdes_50 < 1.0, f"MDES for n=50 should be around 0.4-0.6, got {mdes_50}"

    def test_power_calculation(self):
        """Test that power increases with effect size."""
        power_small = calculate_power(n=50, effect_size=0.2)
        power_medium = calculate_power(n=50, effect_size=0.5)
        power_large = calculate_power(n=50, effect_size=0.8)

        assert power_small < power_medium < power_large, "Power should increase with effect size"
        assert 0.0 <= power_small <= 1.0
        assert 0.0 <= power_medium <= 1.0
        assert 0.0 <= power_large <= 1.0

    def test_power_at_threshold(self):
        """Test that power is approximately 0.8 when effect size equals MDES."""
        mdes = calculate_mdes(n=50)
        power_at_mdes = calculate_power(n=50, effect_size=mdes)
        # Allow some tolerance for approximation errors
        assert 0.75 < power_at_mdes < 0.85, f"Power at MDES should be ~0.8, got {power_at_mdes}"

    def test_mdes_underpowered_for_small_effect(self):
        """Verify that n=50 is underpowered for small effects (< 0.2)."""
        mdes = calculate_mdes(n=50)
        # Standard convention: small effect d=0.2
        # If MDES > 0.2, we are underpowered for small effects.
        assert mdes > 0.2, f"n=50 should be underpowered for small effects (MDES={mdes})"

    def test_invalid_sample_size(self):
        """Test that small sample sizes raise errors or return 0."""
        with pytest.raises(ValueError):
            calculate_mdes(n=2)
        
        # Power for invalid size should be 0
        assert calculate_power(n=2, effect_size=0.5) == 0.0