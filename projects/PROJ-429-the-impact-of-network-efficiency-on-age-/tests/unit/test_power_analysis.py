import pytest
import numpy as np
from stats.power_analysis import calculate_power_for_correlation, find_mdes

class TestPowerAnalysis:
    def test_power_for_large_effect(self):
        """Test power calculation for a large effect size with small N."""
        # With N=50 and r=0.5, power should be high
        power = calculate_power_for_correlation(n=50, rho=0.5)
        assert power > 0.90, f"Expected high power for large effect, got {power}"

    def test_power_for_small_effect(self):
        """Test power calculation for a small effect size with small N."""
        # With N=20 and r=0.1, power should be low
        power = calculate_power_for_correlation(n=20, rho=0.1)
        assert power < 0.20, f"Expected low power for small effect, got {power}"

    def test_power_for_target(self):
        """Test power for the specific target r=0.3 with N=85."""
        # This is a sanity check for the specific scenario in T027
        power = calculate_power_for_correlation(n=85, rho=0.3)
        # Analytical expectation: ~0.76 for N=85, r=0.3, alpha=0.05
        assert 0.70 < power < 0.85, f"Unexpected power for N=85, r=0.3: {power}"

    def test_mdes_monotonicity(self):
        """Test that MDES decreases as N increases."""
        mdes_50 = find_mdes(n=50, target_power=0.80)
        mdes_100 = find_mdes(n=100, target_power=0.80)
        assert mdes_100 < mdes_50, "MDES should decrease as sample size increases"

    def test_mdes_target_power(self):
        """Verify that the found MDES actually yields the target power."""
        n = 80
        target_power = 0.80
        mdes = find_mdes(n=n, target_power=target_power)
        
        # Calculate power for the found MDES
        actual_power = calculate_power_for_correlation(n=n, rho=mdes)
        
        # Allow small tolerance due to binary search precision
        assert abs(actual_power - target_power) < 0.05, \
            f"MDES {mdes} should yield power ~{target_power}, got {actual_power}"

    def test_edge_cases(self):
        """Test edge cases like rho=0 or rho near 1."""
        # rho=0 should yield power ~ alpha
        power_zero = calculate_power_for_correlation(n=50, rho=0.0)
        assert 0.04 < power_zero < 0.06, f"Power for rho=0 should be ~alpha (0.05), got {power_zero}"
        
        # rho near 1 should yield power ~ 1
        power_high = calculate_power_for_correlation(n=20, rho=0.9)
        assert power_high > 0.99, f"Power for high rho should be ~1, got {power_high}"
