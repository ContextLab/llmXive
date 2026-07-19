"""
Unit tests for FR-001 verification in VirtualTactileEstimator.

This module verifies that the core formula k_est = |Torque| / |Velocity|
is correctly implemented in estimator.py, including the epsilon protection
for stiction handling.
"""

import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from estimator import VirtualTactileEstimator
from seed_config import set_seeds


class TestFR001FormulaVerification:
    """
    Tests to verify the implementation of FR-001: k_est = |Torque| / |Velocity|.
    """

    def test_basic_formula_calculation(self):
        """
        Verify that k_est is calculated as |torque| / |velocity| with epsilon.
        
        Given:
          torque = 2.0
          velocity = 0.5
          epsilon = 1e-4 (default)
        
        Expected instantaneous k_est = 2.0 / (0.5 + 1e-4) ≈ 3.9992
        With window_size=1, the smoothed value should be the same.
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 2.0
        velocity = 0.5
        expected_k = abs(torque) / (abs(velocity) + 1e-4)
        
        result = estimator.update(torque, velocity)
        
        # Allow for floating point precision errors
        assert np.isclose(result, expected_k, rtol=1e-5), \
            f"Expected k_est ≈ {expected_k}, got {result}"
        
        assert estimator.get_current_estimate() == result

    def test_formula_with_negative_inputs(self):
        """
        Verify that the formula uses absolute values for torque and velocity.
        
        Given:
          torque = -3.0
          velocity = -1.5
          epsilon = 1e-4
        
        Expected instantaneous k_est = 3.0 / (1.5 + 1e-4) ≈ 1.9998
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = -3.0
        velocity = -1.5
        expected_k = abs(torque) / (abs(velocity) + 1e-4)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected_k, rtol=1e-5), \
            f"Expected k_est ≈ {expected_k}, got {result}"

    def test_formula_with_zero_velocity_stiction(self):
        """
        Verify epsilon clamping prevents division by zero when velocity is 0.
        
        Given:
          torque = 1.0
          velocity = 0.0
          epsilon = 1e-4
        
        Expected instantaneous k_est = 1.0 / (0.0 + 1e-4) = 10000.0
        This tests the stiction handling requirement.
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 1.0
        velocity = 0.0
        expected_k = abs(torque) / (abs(velocity) + 1e-4)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected_k, rtol=1e-5), \
            f"Expected k_est ≈ {expected_k} (stiction case), got {result}"
        
        # Verify the result is finite (not inf or nan)
        assert np.isfinite(result), "k_est should be finite even with zero velocity"

    def test_formula_with_custom_epsilon(self):
        """
        Verify the formula correctly uses the provided epsilon value.
        
        Given:
          torque = 1.0
          velocity = 0.0
          epsilon = 0.01
        
        Expected instantaneous k_est = 1.0 / 0.01 = 100.0
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=0.01)
        
        torque = 1.0
        velocity = 0.0
        expected_k = abs(torque) / (abs(velocity) + 0.01)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected_k, rtol=1e-5), \
            f"Expected k_est ≈ {expected_k} with custom epsilon, got {result}"

    def test_formula_linearity(self):
        """
        Verify that doubling torque doubles the k_est (linearity check).
        
        Given:
          Case 1: torque=1.0, velocity=1.0 -> k_est ≈ 1.0
          Case 2: torque=2.0, velocity=1.0 -> k_est ≈ 2.0
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        # Case 1
        k1 = estimator.update(1.0, 1.0)
        
        # Case 2
        k2 = estimator.update(2.0, 1.0)
        
        # k2 should be approximately 2 * k1
        expected_ratio = 2.0
        actual_ratio = k2 / k1
        
        assert np.isclose(actual_ratio, expected_ratio, rtol=1e-3), \
            f"Expected ratio ≈ {expected_ratio}, got {actual_ratio}"

    def test_formula_with_moving_average(self):
        """
        Verify that the moving average correctly smooths multiple k_est calculations.
        
        Given 3 samples with window_size=3:
          Sample 1: torque=1.0, velocity=1.0 -> k ≈ 1.0
          Sample 2: torque=3.0, velocity=1.0 -> k ≈ 3.0
          Sample 3: torque=2.0, velocity=1.0 -> k ≈ 2.0
        
        Expected smoothed k_est = (1.0 + 3.0 + 2.0) / 3 = 2.0
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=3, epsilon=1e-4)
        
        # Sample 1
        k1 = estimator.update(1.0, 1.0)
        
        # Sample 2
        k2 = estimator.update(3.0, 1.0)
        
        # Sample 3
        k3 = estimator.update(2.0, 1.0)
        
        # Expected average
        expected_avg = (k1 + k2 + k3) / 3.0
        
        assert np.isclose(k3, expected_avg, rtol=1e-5), \
            f"Expected smoothed k_est ≈ {expected_avg}, got {k3}"

    def test_formula_with_infinite_inputs_raises_error(self):
        """
        Verify that non-finite inputs raise a ValueError.
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        with pytest.raises(ValueError):
            estimator.update(float('inf'), 1.0)
        
        with pytest.raises(ValueError):
            estimator.update(1.0, float('nan'))

    def test_formula_precision_with_small_values(self):
        """
        Verify the formula handles very small torque and velocity values correctly.
        
        Given:
          torque = 1e-6
          velocity = 1e-6
          epsilon = 1e-4
        
        Expected instantaneous k_est = 1e-6 / (1e-6 + 1e-4) ≈ 0.0099
        """
        set_seeds(42)
        estimator = VirtualTactileEstimator(window_size=1, epsilon=1e-4)
        
        torque = 1e-6
        velocity = 1e-6
        expected_k = abs(torque) / (abs(velocity) + 1e-4)
        
        result = estimator.update(torque, velocity)
        
        assert np.isclose(result, expected_k, rtol=1e-5), \
            f"Expected k_est ≈ {expected_k} for small values, got {result}"