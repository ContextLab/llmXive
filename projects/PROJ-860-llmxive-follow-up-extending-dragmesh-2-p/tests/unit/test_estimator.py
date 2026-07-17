"""
Unit tests for VirtualTactileEstimator.

Specifically verifies FR-001 implementation: k_est = |Torque| / |Velocity|
and division-by-zero protection (FR-007).
"""
import pytest
import numpy as np
from estimator import VirtualTactileEstimator

class TestFR001Formula:
    """Tests verifying the core FR-001 formula implementation."""

    def test_basic_torque_velocity_ratio(self):
        """
        Verify k_est = |Torque| / |Velocity| for simple inputs.
        
        FR-001 states: k_est = |Torque| / |Velocity|
        With epsilon = 1e-4 (default), for velocity=1.0, the denominator is ~1.0001.
        """
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 2.5
        velocity = 1.0
        
        # Expected: |2.5| / (|1.0| + 1e-4) = 2.5 / 1.0001 ≈ 2.49975
        expected = abs(torque) / (abs(velocity) + estimator.epsilon)
        
        result = estimator.update(torque, velocity)
        
        # Allow small floating point tolerance
        assert np.isclose(result, expected, rtol=1e-5), \
            f"FR-001 formula violation: expected {expected}, got {result}"
    
    def test_negative_torque_handling(self):
        """Verify that negative torque is handled via absolute value (FR-001)."""
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = -3.0
        velocity = 1.0
        
        # Formula uses |Torque|
        expected = abs(torque) / (abs(velocity) + estimator.epsilon)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected, rtol=1e-5), \
            f"FR-001 absolute torque handling failed: expected {expected}, got {result}"
    
    def test_negative_velocity_handling(self):
        """Verify that negative velocity is handled via absolute value (FR-001)."""
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 4.0
        velocity = -2.0
        
        # Formula uses |Velocity|
        expected = abs(torque) / (abs(velocity) + estimator.epsilon)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected, rtol=1e-5), \
            f"FR-001 absolute velocity handling failed: expected {expected}, got {result}"
    
    def test_zero_velocity_epsilon_protection(self):
        """
        Verify epsilon prevents division by zero when velocity is 0.
        
        FR-007 requires epsilon clamping to prevent division by zero.
        """
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 5.0
        velocity = 0.0
        
        # Expected: |5.0| / (0.0 + 1e-4) = 50000.0
        expected = abs(torque) / estimator.epsilon
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected, rtol=1e-5), \
            f"FR-001/FR-007 epsilon protection failed: expected {expected}, got {result}"
    
    def test_moving_average_integration(self):
        """
        Verify that the moving average (FR-006) correctly averages FR-001 calculations.
        
        The formula is applied per-sample, then averaged.
        """
        window_size = 3
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=0.0)
        
        # Sample 1: k = 10 / 2 = 5.0
        estimator.update(10.0, 2.0)
        # Sample 2: k = 12 / 3 = 4.0
        estimator.update(12.0, 3.0)
        # Sample 3: k = 15 / 5 = 3.0
        result = estimator.update(15.0, 5.0)
        
        # Expected average: (5.0 + 4.0 + 3.0) / 3 = 4.0
        expected = (5.0 + 4.0 + 3.0) / 3.0
        
        assert np.isclose(result, expected, rtol=1e-5), \
            f"Moving average of FR-001 values failed: expected {expected}, got {result}"
    
    def test_clamping_applied_after_formula(self):
        """
        Verify that clamping (FR-007) is applied AFTER the formula calculation.
        
        The raw formula result should be clamped to [min_k, max_k].
        """
        estimator = VirtualTactileEstimator(
            window_size=1, 
            epsilon=1e-4, 
            min_k=0.5, 
            max_k=2.0
        )
        
        # This would produce k = 100 / 0.1 = 1000.0 without clamping
        torque = 100.0
        velocity = 0.1
        
        result = estimator.update(torque, velocity)
        
        # Should be clamped to max_k
        assert result == 2.0, \
            f"FR-007 clamping failed: expected 2.0, got {result}"
    
    def test_input_validation_finite(self):
        """Verify that non-finite inputs raise ValueError."""
        estimator = VirtualTactileEstimator()
        
        with pytest.raises(ValueError):
            estimator.update(float('nan'), 1.0)
        
        with pytest.raises(ValueError):
            estimator.update(1.0, float('inf'))

class TestDivisionByZeroProtection:
    """
    Specific tests for division-by-zero protection (T018).
    
    Ensures that when velocity approaches zero, the estimator uses epsilon
    to prevent division by zero and returns a large but finite value.
    """
    
    def test_exact_zero_velocity(self):
        """
        Test that exact zero velocity does not cause ZeroDivisionError.
        
        Instead, it should use epsilon as the denominator.
        """
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-6)
        
        torque = 10.0
        velocity = 0.0
        
        # Should not raise ZeroDivisionError
        result = estimator.update(torque, velocity)
        
        # Verify result is finite and matches expected calculation
        assert np.isfinite(result), "Result should be finite"
        assert not np.isnan(result), "Result should not be NaN"
        assert not np.isinf(result), "Result should not be Inf (clamped by max_k if applicable)"
        
        expected = abs(torque) / estimator.epsilon
        assert np.isclose(result, expected, rtol=1e-5), \
            f"Division by zero protection failed: expected {expected}, got {result}"
    
    def test_very_small_velocity(self):
        """
        Test that very small velocity values are handled correctly.
        
        When velocity is smaller than epsilon, epsilon should dominate the denominator.
        """
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 1.0
        velocity = 1e-10  # Much smaller than epsilon
        
        result = estimator.update(torque, velocity)
        
        # When velocity << epsilon, result should be approximately torque / epsilon
        expected = abs(torque) / estimator.epsilon
        
        assert np.isclose(result, expected, rtol=1e-3), \
            f"Small velocity handling failed: expected ~{expected}, got {result}"
    
    def test_no_division_by_zero_exception(self):
        """
        Explicitly verify that ZeroDivisionError is never raised.
        
        This is the core requirement of T018.
        """
        estimator = VirtualTactileEstimator(window_size=10, epsilon=1e-4)
        
        # Test a sequence of inputs including zero velocity
        test_cases = [
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (10.0, 0.0),
            (0.5, 0.0),
        ]
        
        for torque, velocity in test_cases:
            # This should never raise ZeroDivisionError
            try:
                result = estimator.update(torque, velocity)
                assert np.isfinite(result), f"Result for ({torque}, {velocity}) should be finite"
            except ZeroDivisionError:
                pytest.fail(f"ZeroDivisionError raised for torque={torque}, velocity={velocity}")
    
    def test_epsilon_parameter_effect(self):
        """
        Verify that different epsilon values correctly prevent division by zero.
        
        Larger epsilon should result in smaller k_est for the same zero velocity.
        """
        torque = 1.0
        velocity = 0.0
        
        epsilon_small = 1e-6
        epsilon_large = 1e-2
        
        estimator_small = VirtualTactileEstimator(window_size=1, epsilon=epsilon_small)
        estimator_large = VirtualTactileEstimator(window_size=1, epsilon=epsilon_large)
        
        result_small = estimator_small.update(torque, velocity)
        result_large = estimator_large.update(torque, velocity)
        
        # Expected values
        expected_small = abs(torque) / epsilon_small
        expected_large = abs(torque) / epsilon_large
        
        assert np.isclose(result_small, expected_small), \
            f"Small epsilon protection failed: expected {expected_small}, got {result_small}"
        assert np.isclose(result_large, expected_large), \
            f"Large epsilon protection failed: expected {expected_large}, got {result_large}"
        
        # Verify that larger epsilon gives smaller result
        assert result_large < result_small, \
            f"Larger epsilon should give smaller k_est: {result_large} < {result_small}"
    
    def test_moving_average_with_zero_velocities(self):
        """
        Test moving average calculation when multiple inputs have zero velocity.
        
        Ensures the moving average buffer handles multiple zero-velocity cases correctly.
        """
        window_size = 5
        epsilon = 1e-4
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=epsilon)
        
        # All inputs have zero velocity
        torque_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        velocity_values = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        expected_values = [abs(t) / epsilon for t in torque_values]
        
        for t, v in zip(torque_values, velocity_values):
            estimator.update(t, v)
        
        # The last update should return the average of all 5 values
        result = estimator.update(torque_values[-1], velocity_values[-1])
        expected_avg = sum(expected_values) / window_size
        
        assert np.isclose(result, expected_avg, rtol=1e-5), \
            f"Moving average with zero velocities failed: expected {expected_avg}, got {result}"
    
    def test_boundary_case_velocity_equals_epsilon(self):
        """
        Test when velocity exactly equals epsilon.
        
        This is a boundary case where velocity and epsilon are equal.
        """
        epsilon = 1e-4
        estimator = VirtualTactileEstimator(window_size=1, epsilon=epsilon)
        
        torque = 1.0
        velocity = epsilon  # velocity == epsilon
        
        result = estimator.update(torque, velocity)
        
        # Denominator should be |velocity| + epsilon = 2 * epsilon
        expected = abs(torque) / (2 * epsilon)
        
        assert np.isclose(result, expected, rtol=1e-5), \
            f"Boundary case failed: expected {expected}, got {result}"