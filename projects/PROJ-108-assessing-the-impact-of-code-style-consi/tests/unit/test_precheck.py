"""
Unit tests for pre-check logic in statistical analysis.

This module verifies the effect size gate (> 0.5) required before
proceeding to full statistical analysis (FR-009).
"""
import pytest
import math
from typing import List, Tuple, Optional

# Import the metric function from the project's utility module
# As defined in code/utils/metrics.py
from code.utils.metrics import compute_cohen_d


class TestPrecheckLogic:
    """Tests for the effect size pre-check gate."""

    def test_effect_size_large_positive(self):
        """Verify gate passes when effect size > 0.5 (large positive)."""
        # Simulate two groups with a clear difference
        group_high = [10.0, 11.0, 12.0, 11.5, 10.5]
        group_low = [5.0, 6.0, 5.5, 6.5, 5.0]

        d = compute_cohen_d(group_high, group_low)
        
        # Pre-check logic: gate passes if |d| > 0.5
        assert abs(d) > 0.5, f"Expected effect size > 0.5, got {d}"
        assert d > 0.5, "Expected positive direction for High group"

    def test_effect_size_large_negative(self):
        """Verify gate passes when effect size < -0.5 (large negative)."""
        # Reverse the groups to get a negative effect size
        group_high = [5.0, 6.0, 5.5, 6.5, 5.0]
        group_low = [10.0, 11.0, 12.0, 11.5, 10.5]

        d = compute_cohen_d(group_high, group_low)
        
        # Pre-check logic: gate passes if |d| > 0.5
        assert abs(d) > 0.5, f"Expected effect size magnitude > 0.5, got {d}"
        assert d < -0.5, "Expected negative direction for High group"

    def test_effect_size_medium(self):
        """Verify gate fails when effect size is medium (~0.5)."""
        # Create groups with a medium effect size
        # Cohen's d = (mean1 - mean2) / pooled_std
        # Let's aim for d approx 0.4
        group_high = [10.0, 10.2, 9.8, 10.1, 9.9]
        group_low = [8.0, 8.2, 7.8, 8.1, 7.9]

        d = compute_cohen_d(group_high, group_low)
        
        # Pre-check logic: gate should fail if |d| <= 0.5
        assert abs(d) <= 0.5, f"Expected effect size <= 0.5 for medium case, got {d}"

    def test_effect_size_small(self):
        """Verify gate fails when effect size is small."""
        # Groups with very similar means
        group_high = [10.0, 10.1, 9.9, 10.0, 10.0]
        group_low = [10.0, 9.9, 10.1, 10.0, 10.0]

        d = compute_cohen_d(group_high, group_low)
        
        # Pre-check logic: gate should fail
        assert abs(d) <= 0.5, f"Expected effect size <= 0.5, got {d}"
        # Ideally d should be close to 0
        assert math.isclose(d, 0.0, abs_tol=0.1), "Effect size should be near zero"

    def test_effect_size_zero_variance(self):
        """Verify handling of zero variance in one group."""
        # One group has zero variance
        group_high = [10.0, 10.0, 10.0, 10.0, 10.0]
        group_low = [5.0, 6.0, 7.0, 8.0, 9.0]

        # The function should handle this, potentially returning a large value or raising
        # depending on implementation. We test that it doesn't crash with a division by zero
        # if the implementation handles it, or that it raises a specific error if not.
        # Assuming standard implementation: pooled std won't be zero if one group has variance.
        d = compute_cohen_d(group_high, group_low)
        
        # With group_low having variance, pooled std > 0, so d is calculable.
        # Mean diff = 10 - 7 = 3.
        # Std of low = 1.58. Pooled std approx 1.58. d approx 1.89.
        assert abs(d) > 0.5

    def test_effect_size_both_zero_variance(self):
        """Verify handling when both groups have zero variance."""
        group_high = [10.0, 10.0, 10.0]
        group_low = [5.0, 5.0, 5.0]

        # If both have zero variance, pooled std is 0. 
        # Standard Cohen's d is undefined (division by zero).
        # The metric function should handle this gracefully (e.g., return float('inf') or raise).
        # Here we assume it returns infinity or a large number if means differ.
        d = compute_cohen_d(group_high, group_low)
        
        # If means differ and variance is zero, effect is infinite/undefined.
        # We expect the pre-check to treat this as "significant" or handle the error.
        # If the function returns inf, abs(inf) > 0.5 is True.
        if math.isinf(d):
            assert True # Passes the gate logic conceptually
        else:
            # If it returns a finite number, check threshold
            assert abs(d) > 0.5 or math.isnan(d), "Should handle zero variance case"

    def test_gate_logic_integration(self):
        """Test the full gate logic: pass if |d| > 0.5, else fail."""
        def precheck_gate(effect_size: float) -> bool:
            """Returns True if analysis should proceed."""
            return abs(effect_size) > 0.5

        # Case 1: Large effect -> Proceed
        assert precheck_gate(0.8) is True
        assert precheck_gate(-0.8) is True
        
        # Case 2: Small effect -> Stop
        assert precheck_gate(0.3) is False
        assert precheck_gate(-0.3) is False
        
        # Case 3: Boundary
        assert precheck_gate(0.5) is False
        assert precheck_gate(-0.5) is False
        assert precheck_gate(0.5001) is True

    def test_realistic_scenario_high_vs_low(self):
        """Test with realistic simulated data for High vs Low style groups."""
        # Simulate BLEU scores: High consistency group performs better
        high_group = [25.5, 26.1, 24.8, 25.9, 26.5, 25.0, 26.2, 25.8, 24.9, 26.0]
        low_group = [18.2, 19.5, 17.8, 19.0, 18.5, 19.2, 17.9, 18.8, 19.1, 18.0]

        d = compute_cohen_d(high_group, low_group)
        
        # Verify pre-check passes
        assert precheck_gate(d) is True, "Realistic difference should pass the gate"
        assert d > 0.5, "High group should have higher scores"

def precheck_gate(effect_size: float) -> bool:
    """
    Helper function to encapsulate the pre-check logic.
    
    Args:
        effect_size: Cohen's d value.
        
    Returns:
        True if |effect_size| > 0.5, False otherwise.
    """
    return abs(effect_size) > 0.5