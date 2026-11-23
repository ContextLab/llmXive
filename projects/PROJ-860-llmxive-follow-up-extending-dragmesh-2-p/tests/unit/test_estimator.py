import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from estimator import VirtualTactileEstimator

class TestDivisionByZeroProtection:
    """
    Unit tests for VirtualTactileEstimator division-by-zero protection.
    
    Verifies that the estimator applies epsilon clamping to the denominator
    (velocity) to prevent division by zero, ensuring k_est remains finite
    even when velocity is exactly zero or near-zero.
    
    This addresses FR-001 and the stiction handling requirement.
    """

    def test_exact_zero_velocity(self):
        """Test that exact zero velocity does not raise ZeroDivisionError."""
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        # Provide a non-zero torque with zero velocity
        torque = 1.0
        velocity = 0.0
        
        # This should NOT raise an exception
        k_est = estimator.update(torque, velocity)
        
        # k_est should be finite and high (due to epsilon in denominator)
        assert np.isfinite(k_est), "k_est should be finite when velocity is zero"
        assert k_est > 0, "k_est should be positive"
        
        # Verify the value matches expected calculation: torque / epsilon
        expected = torque / estimator.epsilon
        np.testing.assert_almost_equal(k_est, expected, decimal=5)

    def test_near_zero_velocity(self):
        """Test behavior with very small velocity values."""
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        torque = 0.5
        velocity = 1e-10  # Much smaller than epsilon
        
        k_est = estimator.update(torque, velocity)
        
        # Should be finite and dominated by epsilon
        assert np.isfinite(k_est)
        assert k_est > 0

    def test_moving_average_with_zero_velocity(self):
        """Test that moving average filter handles zero velocities correctly."""
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        # Feed a sequence including zeros
        sequence = [
            (1.0, 1.0),   # Normal
            (1.0, 0.0),   # Zero velocity
            (1.0, 0.5),   # Normal
            (1.0, 0.0),   # Zero velocity
            (1.0, 0.2),   # Normal
        ]
        
        results = []
        for torque, velocity in sequence:
            k_est = estimator.update(torque, velocity)
            results.append(k_est)
            assert np.isfinite(k_est), f"k_est became non-finite at step {len(results)}"
        
        # The moving average should smooth the spikes from zero velocity
        assert len(results) == 5
        # Last value should be an average of the last 5 (all valid)
        assert np.isfinite(results[-1])

    def test_epsilon_parameter_respected(self):
        """Test that the epsilon parameter is actually used in clamping."""
        # Test with a larger epsilon
        estimator_large_eps = VirtualTactileEstimator(window_size=5, epsilon=1e-2)
        k_est_large = estimator_large_eps.update(1.0, 0.0)
        
        # Test with default epsilon
        estimator_default = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        k_est_default = estimator_default.update(1.0, 0.0)
        
        # The one with larger epsilon should have smaller k_est (1/eps)
        assert k_est_large < k_est_default, \
            f"Larger epsilon should result in smaller k_est: {k_est_large} vs {k_est_default}"
        
        # Verify exact values
        expected_large = 1.0 / 1e-2
        expected_default = 1.0 / 1e-4
        
        np.testing.assert_almost_equal(k_est_large, expected_large, decimal=5)
        np.testing.assert_almost_equal(k_est_default, expected_default, decimal=5)

    def test_no_inf_or_nan_in_normal_operation(self):
        """Ensure normal operation doesn't produce inf/nan."""
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        # Normal range values
        for _ in range(10):
            torque = np.random.uniform(0.1, 5.0)
            velocity = np.random.uniform(0.1, 2.0)
            k_est = estimator.update(torque, velocity)
            assert np.isfinite(k_est), "Normal operation produced non-finite value"
            assert not np.isnan(k_est), "Normal operation produced NaN"
            assert not np.isinf(k_est), "Normal operation produced Inf"

    def test_stiction_detection_trigger(self):
        """
        Verify that high k_est values (triggered by zero velocity) 
        indicate stiction as per FR-001.
        """
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        # Simulate stiction: high torque, zero velocity
        k_est_stiction = estimator.update(torque=2.0, velocity=0.0)
        
        # This should result in a very high stiffness estimate
        # (2.0 / 1e-4 = 20000)
        assert k_est_stiction > 1000, \
            f"Stiction should produce high k_est, got {k_est_stiction}"
        
        # Simulate sliding: lower torque, higher velocity
        k_est_sliding = estimator.update(torque=0.5, velocity=1.0)
        
        # Sliding should produce lower stiffness
        assert k_est_sliding < k_est_stiction, \
            "Sliding state should have lower k_est than stiction"

class TestMovingAverageFilterSmoothing:
    """
    Unit tests for VirtualTactileEstimator moving average filter smoothing.
    
    Verifies that the estimator correctly implements a sliding window
    moving average to smooth out noise in the stiffness estimate,
    as required by FR-006.
    """

    def test_window_size_initialization(self):
        """Test that the window size is correctly set and used."""
        estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
        
        # The internal buffer should be initialized with the correct size
        assert len(estimator.torque_history) == 0  # Initially empty
        assert len(estimator.velocity_history) == 0
        
        # After filling the window, it should have exactly window_size elements
        for _ in range(5):
            estimator.update(1.0, 1.0)
        
        assert len(estimator.torque_history) == 5
        assert len(estimator.velocity_history) == 5

    def test_moving_average_calculation(self):
        """
        Verify that the moving average is correctly calculated.
        
        When the window is full, the estimate should be the average of
        the last window_size samples.
        """
        window_size = 5
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        # Create a sequence where the average is known
        # Torque = 2.0 for all steps, Velocity = 1.0 for all steps
        # k_est for each step = 2.0 / 1.0 = 2.0
        # Moving average should be 2.0
        for _ in range(window_size):
            k_est = estimator.update(2.0, 1.0)
        
        assert np.isclose(k_est, 2.0, atol=1e-6), \
            f"Expected 2.0, got {k_est}"

    def test_moving_average_smoothing_effect(self):
        """
        Test that the moving average smooths out high-frequency noise.
        
        Inject a spike in one sample and verify it is dampened in the output.
        """
        window_size = 5
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        # Sequence: 4 normal samples, 1 spike, then continue
        # Normal: torque=1.0, velocity=1.0 -> k=1.0
        # Spike: torque=10.0, velocity=1.0 -> k=10.0
        
        # Fill with normal data
        for _ in range(window_size - 1):
            estimator.update(1.0, 1.0)
        
        # Add the spike
        k_spike = estimator.update(10.0, 1.0)
        
        # The spike should be present but averaged with previous 4 samples of 1.0
        # Expected average = (4 * 1.0 + 1 * 10.0) / 5 = 14.0 / 5 = 2.8
        expected_avg = (4 * 1.0 + 10.0) / 5.0
        
        assert np.isclose(k_spike, expected_avg, atol=1e-6), \
            f"Moving average failed to smooth spike. Expected {expected_avg}, got {k_spike}"

    def test_window_rollover_behavior(self):
        """
        Test that old samples are correctly removed when the window is full.
        
        When a new sample is added after the window is full, the oldest
        sample should be removed from the average.
        """
        window_size = 3
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        # Step 1: Fill window with value 1.0 (k=1.0)
        # Step 2: Fill window with value 2.0 (k=2.0)
        # Step 3: Add value 3.0 (k=3.0)
        
        # After 3 steps: [1, 1, 1] -> avg = 1.0
        estimator.update(1.0, 1.0)
        estimator.update(1.0, 1.0)
        k1 = estimator.update(1.0, 1.0)
        assert np.isclose(k1, 1.0, atol=1e-6)
        
        # After 4 steps: [1, 1, 2] -> avg = 4/3 = 1.333...
        # (We update with torque=2.0, velocity=1.0 -> k=2.0)
        k2 = estimator.update(2.0, 1.0)
        expected2 = (1.0 + 1.0 + 2.0) / 3.0
        assert np.isclose(k2, expected2, atol=1e-6)
        
        # After 5 steps: [1, 2, 3] -> avg = 6/3 = 2.0
        # (We update with torque=3.0, velocity=1.0 -> k=3.0)
        k3 = estimator.update(3.0, 1.0)
        expected3 = (1.0 + 2.0 + 3.0) / 3.0
        assert np.isclose(k3, expected3, atol=1e-6)

    def test_noise_reduction_vs_single_sample(self):
        """
        Compare the variance of the moving average estimate vs a single sample.
        
        With injected noise, the moving average should have lower variance
        than individual samples.
        """
        window_size = 10
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        np.random.seed(42)  # Reproducibility
        n_samples = 100
        true_torque = 2.0
        true_velocity = 1.0
        
        # Generate noisy samples
        noisy_torques = true_torque + np.random.normal(0, 0.5, n_samples)
        noisy_velocities = true_velocity + np.random.normal(0, 0.2, n_samples)
        
        # Calculate individual estimates (without smoothing)
        individual_estimates = noisy_torques / noisy_velocities
        
        # Calculate moving average estimates
        ma_estimates = []
        for t, v in zip(noisy_torques, noisy_velocities):
            k_est = estimator.update(t, v)
            ma_estimates.append(k_est)
        
        # Once window is full, compare variances
        ma_estimates_full = ma_estimates[window_size:]
        
        # The moving average should have lower variance than individual samples
        var_individual = np.var(individual_estimates)
        var_ma = np.var(ma_estimates_full)
        
        assert var_ma < var_individual, \
            f"Moving average should reduce variance. MA var: {var_ma}, Individual var: {var_individual}"

    def test_empty_window_behavior(self):
        """
        Test behavior when the window is not yet full.
        
        Before the window is full, the average should be over the available samples.
        """
        window_size = 5
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        # First sample: average of 1 sample
        k1 = estimator.update(1.0, 1.0)  # k=1.0
        assert np.isclose(k1, 1.0, atol=1e-6)
        
        # Second sample: average of 2 samples
        k2 = estimator.update(2.0, 1.0)  # k=2.0, avg = (1+2)/2 = 1.5
        assert np.isclose(k2, 1.5, atol=1e-6)
        
        # Third sample: average of 3 samples
        k3 = estimator.update(3.0, 1.0)  # k=3.0, avg = (1+2+3)/3 = 2.0
        assert np.isclose(k3, 2.0, atol=1e-6)

    def test_constant_input_constant_output(self):
        """
        Verify that constant input produces constant output after window fill.
        """
        window_size = 5
        estimator = VirtualTactileEstimator(window_size=window_size, epsilon=1e-4)
        
        # Fill window
        for _ in range(window_size):
            estimator.update(5.0, 2.0)  # k = 2.5
        
        # Continue with same input
        results = []
        for _ in range(10):
            k_est = estimator.update(5.0, 2.0)
            results.append(k_est)
        
        # All results should be exactly 2.5
        for i, r in enumerate(results):
            assert np.isclose(r, 2.5, atol=1e-6), \
                f"Step {i}: Expected 2.5, got {r}"