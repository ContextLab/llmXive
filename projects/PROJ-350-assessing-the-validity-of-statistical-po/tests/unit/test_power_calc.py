"""
Unit tests for code/power_calc.py focusing on edge cases and clamping logic.

Tests verify that sensitivity power calculations handle:
- Power > 1.0 (clamped to 1.0)
- Power < 0.0 (clamped to 0.0)
- Extreme sample sizes
- Zero or negative effect sizes
- Invalid alpha values (though FR-003 hardcodes alpha=0.05)
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.power_calc import calculate_sensitivity_power, clamp_power, PowerCalculationError


class TestClampPower:
    """Tests for the clamping logic of power values."""

    def test_power_greater_than_one_clamped(self):
        """Verify power > 1.0 is clamped to 1.0."""
        input_power = 1.5
        expected = 1.0
        result = clamp_power(input_power)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_power_less_than_zero_clamped(self):
        """Verify power < 0.0 is clamped to 0.0."""
        input_power = -0.2
        expected = 0.0
        result = clamp_power(input_power)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_power_within_range_unchanged(self):
        """Verify power within [0, 1] is unchanged."""
        input_power = 0.85
        result = clamp_power(input_power)
        assert result == input_power, f"Expected {input_power}, got {result}"

    def test_power_exact_boundary_zero(self):
        """Verify power exactly 0.0 is unchanged."""
        input_power = 0.0
        result = clamp_power(input_power)
        assert result == input_power

    def test_power_exact_boundary_one(self):
        """Verify power exactly 1.0 is unchanged."""
        input_power = 1.0
        result = clamp_power(input_power)
        assert result == input_power


class TestCalculateSensitivityPowerEdgeCases:
    """Tests for edge cases in sensitivity power calculation."""

    def test_very_large_sample_size(self):
        """Test that very large sample sizes do not cause overflow."""
        # Large N should yield power close to 1.0
        n = 10000
        effect_size = 0.3
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        # Power should be clamped to 1.0 if calculation exceeds it
        assert 0.0 <= result <= 1.0, f"Power {result} out of valid range [0, 1]"

    def test_very_small_sample_size(self):
        """Test that very small sample sizes do not cause errors."""
        # Small N should yield low power
        n = 5
        effect_size = 0.3
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        assert 0.0 <= result <= 1.0, f"Power {result} out of valid range [0, 1]"

    def test_zero_effect_size(self):
        """Test behavior when effect size is zero."""
        n = 50
        effect_size = 0.0
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        # With zero effect size, power should be approximately alpha (Type I error rate)
        # or very close to it depending on the test implementation
        assert 0.0 <= result <= 1.0, f"Power {result} out of valid range [0, 1]"

    def test_negative_effect_size(self):
        """Test behavior when effect size is negative (absolute value used)."""
        n = 50
        effect_size = -0.3
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        # Should handle absolute value internally
        assert 0.0 <= result <= 1.0, f"Power {result} out of valid range [0, 1]"

    def test_extreme_effect_size(self):
        """Test behavior with very large effect size."""
        n = 20
        effect_size = 5.0  # Extremely large
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        # Should be clamped to 1.0
        assert result == 1.0, f"Expected 1.0 for extreme effect, got {result}"

    def test_invalid_sample_size_zero(self):
        """Test that zero sample size raises an error."""
        n = 0
        effect_size = 0.3
        alpha = 0.05
        with pytest.raises(PowerCalculationError):
            calculate_sensitivity_power(n, effect_size, alpha)

    def test_invalid_sample_size_negative(self):
        """Test that negative sample size raises an error."""
        n = -10
        effect_size = 0.3
        alpha = 0.05
        with pytest.raises(PowerCalculationError):
            calculate_sensitivity_power(n, effect_size, alpha)

    def test_invalid_effect_size_nan(self):
        """Test that NaN effect size raises an error."""
        n = 50
        effect_size = float('nan')
        alpha = 0.05
        with pytest.raises(PowerCalculationError):
            calculate_sensitivity_power(n, effect_size, alpha)

    def test_invalid_alpha_zero(self):
        """Test that alpha=0 raises an error."""
        n = 50
        effect_size = 0.3
        alpha = 0.0
        with pytest.raises(PowerCalculationError):
            calculate_sensitivity_power(n, effect_size, alpha)

    def test_invalid_alpha_greater_than_one(self):
        """Test that alpha > 1 raises an error."""
        n = 50
        effect_size = 0.3
        alpha = 1.5
        with pytest.raises(PowerCalculationError):
            calculate_sensitivity_power(n, effect_size, alpha)


class TestClampingIntegration:
    """Integration tests ensuring clamping happens within the calculation flow."""

    def test_calculation_returns_clamped_value_high(self):
        """Verify that the main function returns clamped values for high power."""
        # Parameters likely to produce power > 1.0 before clamping
        n = 5000
        effect_size = 0.8
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        assert result == 1.0, f"Expected 1.0 (clamped), got {result}"

    def test_calculation_returns_clamped_value_low(self):
        """Verify that the main function returns clamped values for low power."""
        # Parameters likely to produce power < 0.0 before clamping (if possible)
        # Though typical power calc won't go below 0, we test the boundary
        n = 2
        effect_size = 0.0001
        alpha = 0.05
        result = calculate_sensitivity_power(n, effect_size, alpha)
        assert 0.0 <= result <= 1.0, f"Power {result} out of valid range [0, 1]"