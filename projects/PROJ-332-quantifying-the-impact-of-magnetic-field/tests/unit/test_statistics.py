"""
Unit tests for Power Analysis logic in code/analysis/correlation.py.

This test suite validates the power calculation functions required by T028 and FR-008.
It verifies:
1. calculate_power returns expected values for known effect sizes and sample sizes.
2. check_power_sufficiency correctly flags results based on the 20% threshold.
3. The logic integrates correctly with the correlation analysis parameters.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from scipy import stats

# Import the specific functions under test from the existing API surface
from code.analysis.correlation import calculate_power, check_power_sufficiency


class TestCalculatePower:
    """Tests for the calculate_power function."""

    def test_power_increases_with_sample_size(self):
        """
        Verify that power increases as sample size increases,
        holding effect size and alpha constant.
        """
        effect_size = 0.5
        alpha = 0.05
        
        power_n10 = calculate_power(effect_size=effect_size, n=10, alpha=alpha)
        power_n50 = calculate_power(effect_size=effect_size, n=50, alpha=alpha)
        power_n100 = calculate_power(effect_size=effect_size, n=100, alpha=alpha)
        
        assert 0 <= power_n10 <= 1, "Power must be between 0 and 1"
        assert 0 <= power_n50 <= 1, "Power must be between 0 and 1"
        assert 0 <= power_n100 <= 1, "Power must be between 0 and 1"
        
        # Power should strictly increase with N for a fixed effect size
        assert power_n50 > power_n10, "Power should increase with sample size"
        assert power_n100 > power_n50, "Power should increase with sample size"

    def test_power_increases_with_effect_size(self):
        """
        Verify that power increases as effect size increases,
        holding sample size and alpha constant.
        """
        n = 30
        alpha = 0.05
        
        power_small = calculate_power(effect_size=0.2, n=n, alpha=alpha)
        power_medium = calculate_power(effect_size=0.5, n=n, alpha=alpha)
        power_large = calculate_power(effect_size=0.8, n=n, alpha=alpha)
        
        assert power_medium > power_small, "Power should increase with effect size"
        assert power_large > power_medium, "Power should increase with effect size"

    def test_power_decreases_with_alpha(self):
        """
        Verify that power decreases as alpha (significance level) decreases,
        making the test more conservative.
        """
        effect_size = 0.5
        n = 50
        
        power_alpha_05 = calculate_power(effect_size=effect_size, n=n, alpha=0.05)
        power_alpha_01 = calculate_power(effect_size=effect_size, n=n, alpha=0.01)
        
        # Lower alpha (stricter threshold) reduces power
        assert power_alpha_05 > power_alpha_01, "Power should decrease with stricter alpha"

    def test_power_near_zero_for_n_one(self):
        """
        Verify that with a sample size of 1, power is effectively zero.
        """
        power = calculate_power(effect_size=0.5, n=1, alpha=0.05)
        # With N=1, correlation is undefined or power is 0.
        # Depending on implementation, it might be 0 or raise. 
        # Assuming it returns 0 or a very small number.
        assert power == 0.0 or power < 0.01, "Power with N=1 should be negligible"

    def test_power_near_one_for_large_n_and_effect(self):
        """
        Verify that with a very large sample size and large effect,
        power approaches 1.0.
        """
        power = calculate_power(effect_size=0.8, n=1000, alpha=0.05)
        assert power > 0.99, "Power should be near 1.0 for large N and effect"


class TestCheckPowerSufficiency:
    """Tests for the check_power_sufficiency function."""

    def test_returns_high_power_flag(self):
        """
        Verify that sufficient power (>= 0.20) returns 'Sufficient'.
        """
        # Simulate a scenario with decent power
        power_val = 0.85
        result = check_power_sufficiency(power=power_val)
        
        assert result['status'] == 'Sufficient', "Status should be 'Sufficient'"
        assert result['flag'] is False, "Flag should be False (no warning)"
        assert result['message'] == ""

    def test_returns_low_power_flag(self):
        """
        Verify that low power (< 0.20) returns 'Inconclusive' and sets flag.
        """
        # Simulate a scenario with low power
        power_val = 0.15
        result = check_power_sufficiency(power=power_val)
        
        assert result['status'] == 'Inconclusive due to low power', "Status should indicate low power"
        assert result['flag'] is True, "Flag should be True (warning)"
        assert "low power" in result['message'].lower(), "Message should mention low power"

    def test_boundary_condition_exactly_20_percent(self):
        """
        Verify behavior exactly at the 20% threshold.
        """
        power_val = 0.20
        result = check_power_sufficiency(power=power_val)
        
        # Assuming >= 0.20 is sufficient
        assert result['status'] == 'Sufficient', "Status should be 'Sufficient' at 20%"
        assert result['flag'] is False

    def test_boundary_condition_below_20_percent(self):
        """
        Verify behavior just below the 20% threshold.
        """
        power_val = 0.199
        result = check_power_sufficiency(power=power_val)
        
        assert result['status'] == 'Inconclusive due to low power', "Status should be 'Inconclusive'"
        assert result['flag'] is True


class TestIntegration:
    """Integration tests ensuring the functions work together as expected."""

    def test_workflow_simulation(self):
        """
        Simulate the workflow described in T028:
        1. Calculate power for a given N and effect size.
        2. Check sufficiency.
        3. Ensure the output structure matches requirements.
        """
        n_samples = 15
        effect_size = 0.5
        alpha = 0.05

        # Step 1: Calculate
        power = calculate_power(effect_size=effect_size, n=n_samples, alpha=alpha)
        
        # Step 2: Check
        check_result = check_power_sufficiency(power=power)
        
        # Step 3: Validate structure
        assert 'status' in check_result
        assert 'flag' in check_result
        assert 'message' in check_result
        
        # Step 4: Validate logic
        if power < 0.20:
            assert check_result['flag'] is True
            assert check_result['status'] == 'Inconclusive due to low power'
        else:
            assert check_result['flag'] is False