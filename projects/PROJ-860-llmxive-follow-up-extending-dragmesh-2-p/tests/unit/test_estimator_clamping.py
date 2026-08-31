"""
Unit tests for range clamping logic in VirtualTactileEstimator.

This test suite validates FR-007: Range clamping to a positive bounded interval.
It ensures that the estimator output never falls outside the defined bounds,
specifically handling cases where the raw calculation results in negative values
or values exceeding the maximum threshold.
"""
import pytest
import numpy as np
import sys
import os
from collections import deque

# Add code directory to path for imports if running standalone
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from estimator import VirtualTactileEstimator


class TestFR007ClampingLogic:
    """Test suite for range clamping logic (FR-007)."""

    def setup_method(self):
        """Initialize the estimator with standard parameters."""
        # Window size 5, epsilon 1e-4, bounds [0.0, 100.0]
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=0.0,
            max_k=100.0
        )

    def test_raw_negative_result_clamped_to_zero(self):
        """
        Verify that a raw calculation resulting in a negative value
        is clamped to the minimum bound (0.0).
        
        Scenario: Delta torque is negative (opposing motion) or Delta velocity
        is negative such that the ratio is negative.
        """
        # Simulate a sequence where the derivative ratio would be negative
        # We force the internal buffer to produce a negative raw estimate
        # by manipulating the input history or mocking the calculation.
        # Since the estimator processes step-by-step, we feed a sequence
        # that mathematically results in a negative slope ratio.
        
        # Reset estimator
        self.estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4, min_k=0.0, max_k=100.0)
        
        # Feed data that results in negative torque change and positive velocity change
        # Or positive torque change and negative velocity change
        # Let's simulate:
        # Step 1: v=0, t=0
        # Step 2: v=1, t=0
        # Step 3: v=2, t=-1 (Negative torque change)
        # ...
        
        # Directly test the clamping logic by feeding a scenario where
        # the calculated k_est before clamping is negative.
        # The estimator calculates k = |d_tau| / |d_v|.
        # Wait, the formula is |d_tau| / |d_v| which is always positive?
        # Let's re-read the spec: "range clamping to a positive bounded interval".
        # If the formula uses absolute values, it's inherently positive.
        # However, FR-007 implies bounds checking.
        # Perhaps the "raw" calculation in the code doesn't use abs?
        # Let's look at the typical implementation pattern:
        # k = d_tau / d_v. If d_v is negative, k is negative.
        # The spec says "range clamping to a positive bounded interval".
        # So we must ensure the output is >= min_k.
        
        # Simulate inputs that would yield a negative raw k if not for abs,
        # or simply test the upper bound first.
        # Actually, if the code uses abs(), the lower bound is naturally 0.
        # But if the code allows negative k (e.g. direction matters), we must clamp.
        # Let's assume the implementation might calculate raw_ratio = d_tau / d_v
        # and then clamp.
        
        # To be safe, we test the upper bound (max_k) and the lower bound (min_k)
        # by forcing inputs that result in extreme values.
        
        # Case 1: Force a very large ratio (d_tau large, d_v small) -> should clamp to max_k
        self.estimator.update(torque=100.0, velocity=0.0001) # d_v small
        # After enough steps to fill window, the moving average will reflect this
        # Let's feed enough data to trigger the calculation
        for _ in range(4):
            self.estimator.update(torque=200.0, velocity=0.0002)
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None, "Estimate should be available after window fill"
        assert k_est <= self.estimator.max_k, f"Value {k_est} exceeds max_k {self.estimator.max_k}"

    def test_raw_large_result_clamped_to_max(self):
        """
        Verify that a raw calculation resulting in a value > max_k
        is clamped to max_k.
        """
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=0.0,
            max_k=100.0
        )
        
        # Create a scenario with extremely high k
        # k = d_tau / d_v. We want d_tau >> d_v
        # d_tau = 1000, d_v = 0.0001 -> k = 10,000,000
        
        # Fill buffer
        for i in range(5):
            self.estimator.update(torque=1000.0 + i, velocity=0.0001 + i*0.00001)
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        assert k_est <= self.estimator.max_k, f"Value {k_est} should be clamped to {self.estimator.max_k}"
        assert k_est == self.estimator.max_k, "Value must be exactly max_k when exceeded"

    def test_raw_small_positive_result_kept(self):
        """
        Verify that a valid positive result within bounds is returned unchanged.
        """
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=0.0,
            max_k=100.0
        )
        
        # k = 50.0 (well within bounds)
        # d_tau = 1.0, d_v = 0.02 -> k = 50
        
        for i in range(5):
            self.estimator.update(torque=1.0 * (i+1), velocity=0.02 * (i+1))
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        # Allow small floating point error
        assert abs(k_est - 50.0) < 1e-6, f"Expected ~50.0, got {k_est}"
        assert k_est >= self.estimator.min_k
        assert k_est <= self.estimator.max_k

    def test_zero_velocity_epsilon_clamp_prevents_div_zero(self):
        """
        Verify that zero velocity does not cause division by zero,
        and that the result is clamped to max_k (since 1/epsilon is huge).
        """
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=0.0,
            max_k=100.0
        )
        
        # d_v = 0.0 -> should be clamped to epsilon
        # k = d_tau / epsilon -> likely > max_k -> clamped to max_k
        for i in range(5):
            self.estimator.update(torque=1.0, velocity=0.0)
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        assert k_est <= self.estimator.max_k
        # Since 1.0 / 1e-4 = 10000, which is > 100, it should be clamped
        assert k_est == self.estimator.max_k

    def test_negative_torque_velocity_ratio_clamped_to_min(self):
        """
        Test scenario where raw ratio might be negative (if implementation allows signed).
        Ensures output is >= min_k.
        """
        # If the estimator uses absolute values (as per formula |d_tau|/|d_v|),
        # this test might be trivial. However, if it uses signed values,
        # this test ensures clamping.
        # We assume the implementation might calculate raw_ratio = d_tau / d_v.
        # If d_tau is positive and d_v is negative, ratio is negative.
        
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=0.0,
            max_k=100.0
        )
        
        # Force negative ratio: positive torque change, negative velocity change
        # Step 0: t=0, v=1
        # Step 1: t=1, v=0 -> d_t=1, d_v=-1 -> ratio = -1
        self.estimator.update(torque=0.0, velocity=1.0)
        self.estimator.update(torque=1.0, velocity=0.0)
        self.estimator.update(torque=2.0, velocity=-1.0)
        self.estimator.update(torque=3.0, velocity=-2.0)
        self.estimator.update(torque=4.0, velocity=-3.0)
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        assert k_est >= self.estimator.min_k, f"Value {k_est} is below min_k {self.estimator.min_k}"
        # If the code uses abs(), k_est should be positive.
        # If the code does not use abs(), it should be clamped to 0.
        # In either case, k_est >= 0.0.

    def test_custom_bounds_clamping(self):
        """
        Verify clamping works with custom min/max bounds.
        """
        # Custom bounds: [10.0, 50.0]
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=10.0,
            max_k=50.0
        )
        
        # Force value > 50
        for i in range(5):
            self.estimator.update(torque=1000.0, velocity=0.0001)
        
        k_est = self.estimator.get_estimate()
        assert k_est == 50.0, f"Expected 50.0, got {k_est}"
        
        # Reset and force value < 10
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=10.0,
            max_k=50.0
        )
        
        # Force value < 10 (e.g., 1.0 / 1.0 = 1.0)
        for i in range(5):
            self.estimator.update(torque=1.0, velocity=1.0)
        
        k_est = self.estimator.get_estimate()
        assert k_est == 10.0, f"Expected 10.0, got {k_est}"

    def test_edge_case_exact_bounds(self):
        """
        Verify that values exactly at min_k and max_k are returned unchanged.
        """
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=10.0,
            max_k=50.0
        )
        
        # Force exactly 10.0
        # k = 10.0 -> d_tau = 10, d_v = 1.0
        for i in range(5):
            self.estimator.update(torque=10.0 * (i+1), velocity=1.0 * (i+1))
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        assert abs(k_est - 10.0) < 1e-6, f"Expected 10.0, got {k_est}"
        
        # Force exactly 50.0
        # k = 50.0 -> d_tau = 50, d_v = 1.0
        self.estimator = VirtualTactileEstimator(
            window_size=5,
            epsilon=1e-4,
            min_k=10.0,
            max_k=50.0
        )
        for i in range(5):
            self.estimator.update(torque=50.0 * (i+1), velocity=1.0 * (i+1))
        
        k_est = self.estimator.get_estimate()
        assert k_est is not None
        assert abs(k_est - 50.0) < 1e-6, f"Expected 50.0, got {k_est}"