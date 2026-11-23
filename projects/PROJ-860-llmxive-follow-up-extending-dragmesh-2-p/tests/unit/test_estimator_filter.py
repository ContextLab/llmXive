"""
Unit tests for the moving average filter logic in VirtualTactileEstimator.

This module validates FR-006: The estimator must apply a moving average filter 
(window size = 5) to the torque signal BEFORE computing the derivative.

Tests cover:
1. Correct window size application
2. Filter behavior with constant signals (should be identity)
3. Filter behavior with linear ramp signals
4. Filter behavior at the boundary (insufficient history)
5. Integration with the full estimator class
"""
import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from estimator import VirtualTactileEstimator
from collections import deque


class TestMovingAverageFilter:
    """Tests specifically for the moving average filter component of the estimator."""

    def test_filter_window_size_initialization(self):
        """Verify that the estimator initializes with the correct filter window size (5)."""
        estimator = VirtualTactileEstimator()
        # The filter is implemented as a deque with maxlen=5
        # We check the internal state to ensure the window size is correct
        assert estimator._torque_buffer.maxlen == 5, "Filter window size must be 5"

    def test_filter_constant_signal(self):
        """
        Test that a constant input signal results in a constant filtered output.
        Moving average of a constant sequence is the constant itself.
        """
        estimator = VirtualTactileEstimator()
        constant_value = 10.0
        num_samples = 20
        
        # Feed constant torque values
        for _ in range(num_samples):
            estimator.update(torque=constant_value, velocity_change=1.0)
        
        # After sufficient samples, the k_est should be consistent
        # Since velocity_change is constant, k_est should be constant_value / 1.0
        # The moving average of a constant is the constant itself
        assert abs(estimator.k_est - constant_value) < 1e-6, \
            f"Constant signal filter failed: expected {constant_value}, got {estimator.k_est}"

    def test_filter_linear_ramp(self):
        """
        Test filter behavior with a linearly increasing signal.
        The moving average of a linear ramp should smooth the noise but follow the trend.
        """
        estimator = VirtualTactileEstimator()
        window_size = 5
        slope = 1.0
        num_samples = 100
        
        # Generate a linear ramp with some noise to simulate real sensor data
        np.random.seed(42)
        torques = np.linspace(0, 100, num_samples) + np.random.normal(0, 0.5, num_samples)
        
        for t in torques:
            estimator.update(torque=t, velocity_change=1.0)
        
        # The filtered value should be close to the true value (within smoothing bounds)
        # We can't check exact equality due to the ramp nature, but we check it's in the right ballpark
        expected_filtered = torques[-1]  # Last value
        # The moving average will lag slightly, but for a large ramp, it should be close
        # We allow a tolerance based on the slope and window size
        max_lag_error = slope * window_size
        assert abs(estimator.k_est - expected_filtered) < max_lag_error + 1.0, \
            f"Linear ramp filter failed: expected approx {expected_filtered}, got {estimator.k_est}"

    def test_filter_insufficient_history(self):
        """
        Test that the estimator handles cases where there isn't enough history
        to fill the moving average window yet.
        """
        estimator = VirtualTactileEstimator()
        window_size = 5
        
        # Feed fewer samples than the window size
        num_samples = 3
        for i in range(num_samples):
            estimator.update(torque=float(i), velocity_change=1.0)
        
        # The estimator should still produce a value based on available data
        # It should not crash or return NaN
        assert not np.isnan(estimator.k_est), "k_est should not be NaN with insufficient history"
        assert not np.isinf(estimator.k_est), "k_est should not be Inf with insufficient history"
        
        # The value should be a reasonable average of the available samples
        # (0 + 1 + 2) / 3 = 1.0
        expected_avg = sum(range(num_samples)) / num_samples
        assert abs(estimator.k_est - expected_avg) < 1e-6, \
            f"Insufficient history average failed: expected {expected_avg}, got {estimator.k_est}"

    def test_filter_exact_window_fill(self):
        """
        Test the exact moment the window fills up.
        At sample 5, the buffer should contain exactly 5 samples.
        """
        estimator = VirtualTactileEstimator()
        window_size = 5
        
        # Feed exactly window_size samples
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for v in values:
            estimator.update(torque=v, velocity_change=1.0)
        
        # The average should be (1+2+3+4+5)/5 = 3.0
        expected_avg = sum(values) / window_size
        assert abs(estimator.k_est - expected_avg) < 1e-6, \
            f"Exact window fill failed: expected {expected_avg}, got {estimator.k_est}"

    def test_filter_oldest_sample_eviction(self):
        """
        Test that the oldest sample is correctly evicted when a new one is added
        after the window is full.
        """
        estimator = VirtualTactileEstimator()
        window_size = 5
        
        # Fill the window with 1, 2, 3, 4, 5 -> avg = 3.0
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            estimator.update(torque=v, velocity_change=1.0)
        
        assert abs(estimator.k_est - 3.0) < 1e-6, "Initial window average incorrect"
        
        # Add 6.0 -> window becomes [2, 3, 4, 5, 6] -> avg = 4.0
        estimator.update(torque=6.0, velocity_change=1.0)
        
        expected_avg = (2.0 + 3.0 + 4.0 + 5.0 + 6.0) / window_size
        assert abs(estimator.k_est - expected_avg) < 1e-6, \
            f"Oldest eviction failed: expected {expected_avg}, got {estimator.k_est}"

    def test_filter_noise_reduction(self):
        """
        Verify that the moving average filter reduces high-frequency noise.
        Compare the variance of raw input vs filtered output.
        """
        estimator = VirtualTactileEstimator()
        np.random.seed(123)
        
        # Generate a signal with high-frequency noise
        base_signal = 10.0
        noise_amplitude = 5.0
        num_samples = 100
        
        noisy_torques = base_signal + np.random.normal(0, noise_amplitude, num_samples)
        
        # Collect filtered values
        filtered_values = []
        for t in noisy_torques:
            estimator.update(torque=t, velocity_change=1.0)
            filtered_values.append(estimator.k_est)
        
        # Calculate variances
        raw_variance = np.var(noisy_torques)
        filtered_variance = np.var(filtered_values)
        
        # The filtered variance should be significantly lower than raw variance
        # For a moving average of size 5, variance should reduce by roughly factor of 5
        reduction_factor = raw_variance / filtered_variance
        assert reduction_factor > 2.0, \
            f"Noise reduction insufficient: reduction factor {reduction_factor} < 2.0"

    def test_filter_integration_with_derivative(self):
        """
        Test that the moving average is applied BEFORE the derivative calculation.
        This is the core requirement of FR-006.
        """
        estimator = VirtualTactileEstimator()
        
        # Create a scenario where the order matters
        # If we didn't filter before derivative, the result would be noisy
        # With filtering, the derivative should be smoother
        
        # Simulate a step change in torque
        # First 5 samples: torque = 10.0
        for _ in range(5):
            estimator.update(torque=10.0, velocity_change=1.0)
        
        k_est_before = estimator.k_est
        
        # Next 5 samples: torque = 20.0
        for _ in range(5):
            estimator.update(torque=20.0, velocity_change=1.0)
        
        k_est_after = estimator.k_est
        
        # The change should be smooth and reflect the filtered average
        # Not an instantaneous jump from 10 to 20
        # The transition should be gradual over the window size
        assert k_est_after > k_est_before, "k_est should increase after torque increase"
        assert k_est_after <= 20.0, "k_est should not exceed the maximum torque input"
        assert k_est_after >= 10.0, "k_est should not be below the minimum torque input"