"""
Unit tests for the reporting module (US3).
Specifically verifies calculate_p_value_shift and apply_bonferroni_correction functionality.
"""
import pytest
import math
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.reporting import calculate_p_value_shift, apply_bonferroni_correction


class TestCalculatePValueShift:
    """Tests for calculate_p_value_shift function."""

    def test_basic_absolute_difference(self):
        """Verify basic absolute difference calculation."""
        baseline = 0.05
        cleaned = 0.02
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(cleaned - baseline)
        assert result == expected

    def test_precision_three_decimals(self):
        """Verify result has at least 3 decimal precision."""
        baseline = 0.051234
        cleaned = 0.023456
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(cleaned - baseline)
        
        # Check that the result matches the expected value to 3 decimal places
        assert math.isclose(result, expected, abs_tol=1e-3)
        
        # Verify we can represent 3 decimal places (string check)
        result_str = f"{result:.3f}"
        assert len(result_str.split('.')[1]) >= 3

    def test_zero_shift(self):
        """Verify zero shift when values are identical."""
        baseline = 0.05
        cleaned = 0.05
        result = calculate_p_value_shift(baseline, cleaned)
        assert result == 0.0

    def test_large_shift(self):
        """Verify calculation with large difference."""
        baseline = 0.001
        cleaned = 0.999
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(0.999 - 0.001)
        assert math.isclose(result, expected, abs_tol=1e-9)

    def test_small_shift_high_precision(self):
        """Verify calculation handles very small shifts correctly."""
        baseline = 0.0500001
        cleaned = 0.0500002
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(cleaned - baseline)
        assert math.isclose(result, expected, abs_tol=1e-10)

    def test_boundary_values(self):
        """Verify calculation at p-value boundaries."""
        # Near 0
        result1 = calculate_p_value_shift(0.0, 0.001)
        assert math.isclose(result1, 0.001, abs_tol=1e-9)
        
        # Near 1
        result2 = calculate_p_value_shift(0.999, 1.0)
        assert math.isclose(result2, 0.001, abs_tol=1e-9)

    def test_invalid_input_type(self):
        """Verify behavior with non-numeric inputs (should raise TypeError)."""
        with pytest.raises(TypeError):
            calculate_p_value_shift("0.05", 0.02)
        
        with pytest.raises(TypeError):
            calculate_p_value_shift(0.05, "0.02")

    def test_negative_p_values(self):
        """Verify handling of negative values (mathematically invalid but function should handle)."""
        baseline = -0.05
        cleaned = 0.02
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(cleaned - baseline)
        assert math.isclose(result, expected, abs_tol=1e-9)

    def test_rounding_behavior(self):
        """Verify that the function does not prematurely round inputs."""
        baseline = 0.05123456789
        cleaned = 0.02123456789
        result = calculate_p_value_shift(baseline, cleaned)
        expected = abs(cleaned - baseline)
        
        # The result should preserve precision before any final formatting
        assert math.isclose(result, expected, abs_tol=1e-9)


class TestApplyBonferroniCorrection:
    """Tests for apply_bonferroni_correction function."""

    def test_basic_correction(self):
        """Verify basic Bonferroni correction logic."""
        p_values = [0.01, 0.05, 0.10]
        m = len(p_values)
        adjusted = apply_bonferroni_correction(p_values)
        
        expected = [min(p * m, 1.0) for p in p_values]
        
        for a, e in zip(adjusted, expected):
            assert math.isclose(a, e, abs_tol=1e-9)

    def test_capping_at_one(self):
        """Verify that adjusted p-values are capped at 1.0."""
        p_values = [0.8, 0.9, 0.95]
        m = len(p_values)
        adjusted = apply_bonferroni_correction(p_values)
        
        for p in adjusted:
            assert p <= 1.0

    def test_single_p_value(self):
        """Verify correction with a single p-value (no change effectively)."""
        p_values = [0.05]
        adjusted = apply_bonferroni_correction(p_values)
        assert math.isclose(adjusted[0], 0.05)

    def test_empty_list_raises(self):
        """Verify that an empty list raises ValueError."""
        with pytest.raises(ValueError):
            apply_bonferroni_correction([])

    def test_invalid_p_value_raises(self):
        """Verify that invalid p-values raise ValueError."""
        with pytest.raises(ValueError):
            apply_bonferroni_correction([0.05, "0.10"])

    def test_p_value_out_of_bounds_clamping(self):
        """Verify that p-values outside [0, 1] are clamped (with warning)."""
        # This test expects the function to clamp and not raise, based on implementation
        p_values = [-0.1, 1.5, 0.05]
        adjusted = apply_bonferroni_correction(p_values)
        
        # -0.1 -> 0.0 -> 0.0 * 3 = 0.0
        # 1.5 -> 1.0 -> 1.0 * 3 = 3.0 -> capped to 1.0
        # 0.05 -> 0.15
        expected = [0.0, 1.0, 0.15]
        
        for a, e in zip(adjusted, expected):
            assert math.isclose(a, e, abs_tol=1e-9)

    def test_correctness_for_fwer(self):
        """Verify that the method controls FWER (conceptual check)."""
        # If we have 20 tests, alpha=0.05, and all raw p=0.002
        # Bonferroni threshold is 0.05/20 = 0.0025
        # Raw 0.002 < 0.0025 -> Significant
        # Adjusted = 0.002 * 20 = 0.04 < 0.05 -> Significant
        p_values = [0.002] * 20
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # All should be significant (adjusted < 0.05)
        for p in adjusted:
            assert p < 0.05

        # If raw p = 0.003
        p_values_high = [0.003] * 20
        adjusted_high = apply_bonferroni_correction(p_values_high, alpha=0.05)
        
        # 0.003 * 20 = 0.06 > 0.05 -> Not significant
        for p in adjusted_high:
            assert p > 0.05