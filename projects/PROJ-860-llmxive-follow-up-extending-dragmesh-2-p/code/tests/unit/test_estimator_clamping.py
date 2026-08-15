"""
Unit tests for FR-007: Bounded Range Clamping logic in VirtualTactileEstimator.

This test suite verifies that the estimator strictly enforces the min_k and max_k
constraints defined in FR-007, ensuring the output never exceeds the bounded range.
"""
import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from estimator import VirtualTactileEstimator


class TestFR007ClampingLogic:
    """Tests for the bounded range clamping (FR-007)."""

    def test_initialization_defaults(self):
        """Verify default clamping bounds."""
        estimator = VirtualTactileEstimator()
        assert estimator.min_k == 0.0
        assert estimator.max_k == 10.0

    def test_custom_bounds_initialization(self):
        """Verify custom bounds are set correctly."""
        estimator = VirtualTactileEstimator(min_k=1.0, max_k=5.0)
        assert estimator.min_k == 1.0
        assert estimator.max_k == 5.0

    def test_clamping_below_min_k(self):
        """
        Verify that a calculated k_est below min_k is clamped to min_k.
        
        Scenario: 
        - torque = 0.01, velocity = 1.0 (instantaneous k = 0.01)
        - min_k = 0.5
        - Expected result: 0.5
        """
        estimator = VirtualTactileEstimator(min_k=0.5, max_k=10.0, window_size=1)
        result = estimator.update(torque=0.01, velocity=1.0)
        
        # The instantaneous k is 0.01, which is < 0.5
        # It should be clamped to 0.5
        assert result == 0.5
        assert result >= estimator.min_k

    def test_clamping_above_max_k(self):
        """
        Verify that a calculated k_est above max_k is clamped to max_k.
        
        Scenario:
        - torque = 100.0, velocity = 0.001 (instantaneous k = 100,000)
        - max_k = 5.0
        - Expected result: 5.0
        Note: epsilon (1e-4) is added, so velocity becomes 0.0011 roughly,
        but the ratio is still massive.
        """
        estimator = VirtualTactileEstimator(min_k=0.0, max_k=5.0, window_size=1, epsilon=1e-4)
        result = estimator.update(torque=100.0, velocity=0.001)
        
        # The instantaneous k is extremely high, > 5.0
        # It should be clamped to 5.0
        assert result == 5.0
        assert result <= estimator.max_k

    def test_value_within_bounds_unchanged(self):
        """
        Verify that a calculated k_est within [min_k, max_k] is returned unchanged.
        
        Scenario:
        - torque = 1.0, velocity = 1.0 (instantaneous k = 1.0)
        - min_k = 0.0, max_k = 10.0
        - Expected result: 1.0
        """
        estimator = VirtualTactileEstimator(min_k=0.0, max_k=10.0, window_size=1)
        result = estimator.update(torque=1.0, velocity=1.0)
        
        # 1.0 is within [0.0, 10.0], so it should be returned as is (within float tolerance)
        assert np.isclose(result, 1.0)

    def test_moving_average_respects_bounds(self):
        """
        Verify that the moving average of values is clamped, not just individual values.
        
        Scenario:
        - 5 samples: 4 samples of k=0.0, 1 sample of k=20.0 (clamped to 10.0 internally? No, 
          the formula clamps the smoothed result).
        - Let's trace:
          1. Update k=0.0 (clamped to 0.0) -> Buffer: [0.0]
          2. Update k=0.0 (clamped to 0.0) -> Buffer: [0.0, 0.0]
          3. Update k=0.0 (clamped to 0.0) -> Buffer: [0.0, 0.0, 0.0]
          4. Update k=0.0 (clamped to 0.0) -> Buffer: [0.0, 0.0, 0.0, 0.0]
          5. Update k=20.0 (clamped to 10.0? No, clamping happens AFTER smoothing in current impl)
          
        Wait, let's re-read the implementation logic in estimator.py:
        1. instantaneous_k calculated.
        2. appended to buffer.
        3. smoothed_k = mean(buffer).
        4. clamped_k = max(min, min(max, smoothed_k)).
        
        So if we have 4 zeros and 1 huge value:
        Buffer: [0, 0, 0, 0, 200000]
        Mean: 40000
        Clamped (max 10.0): 10.0
        
        Let's test this specific flow.
        """
        estimator = VirtualTactileEstimator(min_k=0.0, max_k=10.0, window_size=5)
        
        # Add 4 low values
        estimator.update(0.001, 1.0) # k ~ 0.001
        estimator.update(0.001, 1.0)
        estimator.update(0.001, 1.0)
        estimator.update(0.001, 1.0)
        
        # Add 1 high value
        # torque=100, velocity=0.001 -> k ~ 100,000
        result = estimator.update(100.0, 0.001)
        
        # Mean of ~0 and ~100,000 is ~20,000. 
        # Should be clamped to 10.0
        assert result == 10.0

    def test_stiction_clamping_interaction(self):
        """
        Verify that stiction handling (epsilon) combined with clamping works correctly.
        
        Scenario:
        - velocity = 0.0 (stiction)
        - torque = 0.0001
        - instantaneous_k = 0.0001 / (0 + 1e-4) = 1.0
        - If min_k=2.0, result should be 2.0.
        """
        estimator = VirtualTactileEstimator(min_k=2.0, max_k=10.0, window_size=1, epsilon=1e-4)
        result = estimator.update(torque=0.0001, velocity=0.0)
        
        # instantaneous = 1.0
        # clamped to min 2.0
        assert result == 2.0

    def test_invalid_bounds_initialization(self):
        """Verify that initialization fails if max_k < min_k."""
        with pytest.raises(ValueError):
            VirtualTactileEstimator(min_k=10.0, max_k=5.0)

    def test_boundary_exact_match(self):
        """Verify exact match at boundaries."""
        estimator = VirtualTactileEstimator(min_k=1.0, max_k=5.0, window_size=1)
        
        # Force k=1.0
        # torque=1.0, velocity=1.0 -> k=1.0
        result_min = estimator.update(1.0, 1.0)
        assert result_min == 1.0
        
        # Force k=5.0
        # torque=5.0, velocity=1.0 -> k=5.0
        result_max = estimator.update(5.0, 1.0)
        assert result_max == 5.0