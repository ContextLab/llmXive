"""
Unit tests for epsilon clamping logic in VirtualTactileEstimator.

This module verifies FR-007 compliance: explicit epsilon clamping of the
denominator (velocity derivative) to prevent division by zero or numerical
instability during stiction conditions.

Tests:
- Zero velocity derivative must be clamped to epsilon (1e-4)
- Negative velocity derivative must be clamped to -epsilon (or handled appropriately)
- Very small velocity derivatives must be clamped
- Normal velocity derivatives must pass through unchanged
- Resulting k_est must be bounded and finite
"""
import pytest
import numpy as np
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from estimator import VirtualTactileEstimator


class TestEpsilonClampingLogic:
    """Test suite for epsilon clamping behavior in VirtualTactileEstimator."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.estimator = VirtualTactileEstimator()
        self.epsilon = 1e-4  # Default epsilon value from estimator

    def test_zero_velocity_derivative_clamped_to_epsilon(self):
        """Verify that zero velocity derivative is clamped to epsilon."""
        torque = np.array([1.0, 2.0])
        velocity = np.array([0.0, 0.0])  # Zero velocity change (stiction)

        # Calculate k_est
        k_est = self.estimator.calculate_k_est(torque, velocity)

        # With zero velocity, the derivative is zero, which should be clamped to epsilon
        # k_est = |delta_torque| / epsilon
        expected_delta_torque = abs(torque[1] - torque[0])
        expected_k_est = expected_delta_torque / self.epsilon

        assert np.isfinite(k_est), "k_est must be finite when velocity is zero"
        assert k_est == expected_k_est, f"Expected {expected_k_est}, got {k_est}"

    def test_very_small_velocity_derivative_clamped(self):
        """Verify that velocity derivatives smaller than epsilon are clamped."""
        torque = np.array([1.0, 2.0])
        velocity = np.array([0.0, 1e-6])  # Very small velocity change

        k_est = self.estimator.calculate_k_est(torque, velocity)

        # The velocity derivative (1e-6) is less than epsilon (1e-4), so it should be clamped
        expected_delta_torque = abs(torque[1] - torque[0])
        expected_k_est = expected_delta_torque / self.epsilon

        assert np.isfinite(k_est), "k_est must be finite"
        assert k_est == expected_k_est, f"Expected {expected_k_est}, got {k_est}"

    def test_negative_velocity_derivative_clamped(self):
        """Verify that negative velocity derivatives are handled correctly."""
        torque = np.array([2.0, 1.0])
        velocity = np.array([0.0, -1e-6])  # Small negative velocity change

        k_est = self.estimator.calculate_k_est(torque, velocity)

        # The absolute value of velocity derivative should be clamped to epsilon
        expected_delta_torque = abs(torque[1] - torque[0])
        expected_k_est = expected_delta_torque / self.epsilon

        assert np.isfinite(k_est), "k_est must be finite"
        assert k_est == expected_k_est, f"Expected {expected_k_est}, got {k_est}"

    def test_normal_velocity_derivative_not_clamped(self):
        """Verify that normal velocity derivatives pass through without clamping."""
        torque = np.array([1.0, 2.0])
        velocity = np.array([0.0, 0.1])  # Normal velocity change (>> epsilon)

        k_est = self.estimator.calculate_k_est(torque, velocity)

        # No clamping should occur
        expected_delta_torque = abs(torque[1] - torque[0])
        expected_k_est = expected_delta_torque / 0.1

        assert np.isfinite(k_est), "k_est must be finite"
        assert k_est == expected_k_est, f"Expected {expected_k_est}, got {k_est}"

    def test_epsilon_value_is_correct(self):
        """Verify that the epsilon value used is 1e-4 as specified."""
        # Access the epsilon attribute if exposed, or infer from behavior
        # Since epsilon might be private, we test the behavior directly
        torque = np.array([1.0, 2.0])
        velocity_zero = np.array([0.0, 0.0])
        velocity_small = np.array([0.0, 5e-5])  # Less than 1e-4

        k_zero = self.estimator.calculate_k_est(torque, velocity_zero)
        k_small = self.estimator.calculate_k_est(torque, velocity_small)

        # Both should yield the same result due to clamping
        assert k_zero == k_small, "Zero and small velocity should yield same k_est due to clamping"

        # Verify the clamping value is 1e-4
        expected_delta_torque = 1.0
        expected_clamped_k = expected_delta_torque / 1e-4
        assert k_zero == expected_clamped_k, f"Clamping value should be 1e-4, got {1.0/k_zero}"

    def test_no_infinity_or_nan_in_output(self):
        """Verify that clamping prevents infinity or NaN in k_est."""
        # Test various edge cases that would cause division by zero
        test_cases = [
            (np.array([1.0, 2.0]), np.array([0.0, 0.0])),  # Exact zero
            (np.array([1.0, 2.0]), np.array([0.0, 1e-10])),  # Near zero
            (np.array([1.0, 1.0]), np.array([0.0, 0.0])),  # Zero torque and velocity
            (np.array([1.0, 2.0]), np.array([0.0, -1e-10])),  # Near zero negative
        ]

        for i, (torque, velocity) in enumerate(test_cases):
            k_est = self.estimator.calculate_k_est(torque, velocity)
            assert np.isfinite(k_est), f"Test case {i}: k_est must be finite, got {k_est}"
            assert not np.isnan(k_est), f"Test case {i}: k_est must not be NaN"

    def test_clamping_applied_before_derivative_computation(self):
        """
        Verify that epsilon clamping is applied to the velocity derivative
        before computing k_est, not after.
        """
        # This test ensures the clamping logic is in the right place
        # by checking that very small derivatives are treated as epsilon
        torque = np.array([1.0, 2.0])
        # Use a value much smaller than epsilon to ensure clamping occurs
        velocity = np.array([0.0, 1e-8])

        k_est = self.estimator.calculate_k_est(torque, velocity)

        # If clamping is applied correctly, k_est should be based on epsilon, not 1e-8
        expected_k = 1.0 / 1e-4  # delta_torque / epsilon
        assert k_est == expected_k, f"Clamping should use epsilon (1e-4), not actual small value"

    def test_epsilon_clamping_with_moving_average(self):
        """
        Verify that epsilon clamping works correctly when combined with
        the moving average filter (FR-006).
        """
        # Generate a sequence where the moving average might result in a small value
        torques = np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
        velocities = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # All zero

        # The estimator should handle this without errors
        k_est = self.estimator.calculate_k_est(torques, velocities)

        assert np.isfinite(k_est), "k_est must be finite with moving average and zero velocity"
        assert k_est > 0, "k_est must be positive"

    def test_epsilon_constant_is_1e_4(self):
        """Explicitly verify the epsilon constant value."""
        # Create a scenario where the denominator would be exactly zero
        # and check the resulting k_est matches the expected value with epsilon=1e-4
        torque = np.array([10.0, 20.0])  # delta_torque = 10
        velocity = np.array([0.0, 0.0])

        k_est = self.estimator.calculate_k_est(torque, velocity)

        # k_est = 10 / epsilon => epsilon = 10 / k_est
        inferred_epsilon = 10.0 / k_est

        assert abs(inferred_epsilon - 1e-4) < 1e-10, \
            f"Epsilon should be 1e-4, inferred {inferred_epsilon}"