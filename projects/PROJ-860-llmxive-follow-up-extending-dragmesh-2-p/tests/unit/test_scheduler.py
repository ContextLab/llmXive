"""
Unit tests for AdaptiveRewardScheduler logic.

Tests verify weight scaling logic with explicit predefined thresholds:
- If k_est > 1.0, increase r_detach by >= 20%
- If k_est < 0.2, decrease r_contact by <= 15%
"""
import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from scheduler import AdaptiveRewardScheduler


class TestAdaptiveRewardScheduler:
    """Test suite for AdaptiveRewardScheduler logic."""

    def setup_method(self):
        """Initialize the scheduler before each test."""
        self.scheduler = AdaptiveRewardScheduler()
        self.base_weights = {
            'r_contact': 1.0,
            'r_detach': 1.0,
            'r_smooth': 1.0
        }

    def test_high_stiffness_increase_detach_reward(self):
        """
        Verify that when k_est > 1.0, r_detach is increased by at least 20%.
        This tests the high-friction/stiffness adaptation logic.
        """
        # Test case 1: k_est = 1.5 (clearly > 1.0)
        k_est_high = 1.5
        weights = self.scheduler.get_reward_weights(k_est_high, self.base_weights)
        
        # Expected: r_detach should be >= 1.20 (20% increase)
        expected_min_detach = self.base_weights['r_detach'] * 1.20
        
        assert weights['r_detach'] >= expected_min_detach, \
            f"Expected r_detach >= {expected_min_detach} for k_est={k_est_high}, got {weights['r_detach']}"
        
        # Verify r_contact remains unchanged or decreases slightly (not the focus of this threshold)
        # The spec says "if k_est > 1.0, increase r_detach by >= 20%"
        # It doesn't explicitly mandate r_contact behavior here, but typically it stays base
        assert weights['r_contact'] == self.base_weights['r_contact']

    def test_low_stiffness_decrease_contact_reward(self):
        """
        Verify that when k_est < 0.2, r_contact is decreased by at most 15% (i.e., <= 0.85 of base).
        This tests the low-friction/sliding adaptation logic.
        """
        # Test case 1: k_est = 0.1 (clearly < 0.2)
        k_est_low = 0.1
        weights = self.scheduler.get_reward_weights(k_est_low, self.base_weights)
        
        # Expected: r_contact should be <= 0.85 (15% decrease)
        expected_max_contact = self.base_weights['r_contact'] * 0.85
        
        assert weights['r_contact'] <= expected_max_contact, \
            f"Expected r_contact <= {expected_max_contact} for k_est={k_est_low}, got {weights['r_contact']}"
        
        # Verify r_detach remains unchanged
        assert weights['r_detach'] == self.base_weights['r_detach']

    def test_moderate_stiffness_no_adjustment(self):
        """
        Verify that when 0.2 <= k_est <= 1.0, rewards remain at base values.
        """
        # Test case 1: k_est = 0.5 (within normal range)
        k_est_mod = 0.5
        weights = self.scheduler.get_reward_weights(k_est_mod, self.base_weights)
        
        assert weights['r_contact'] == self.base_weights['r_contact'], \
            f"Expected r_contact = {self.base_weights['r_contact']} for k_est={k_est_mod}, got {weights['r_contact']}"
        assert weights['r_detach'] == self.base_weights['r_detach'], \
            f"Expected r_detach = {self.base_weights['r_detach']} for k_est={k_est_mod}, got {weights['r_detach']}"

    def test_boundary_threshold_high_k(self):
        """
        Verify behavior exactly at the upper threshold (k_est = 1.0).
        According to spec: "if k_est > 1.0", so 1.0 should NOT trigger the increase.
        """
        k_est_boundary = 1.0
        weights = self.scheduler.get_reward_weights(k_est_boundary, self.base_weights)
        
        # At exactly 1.0, no increase should happen (condition is strictly > 1.0)
        assert weights['r_detach'] == self.base_weights['r_detach'], \
            f"Expected no increase at k_est=1.0, got {weights['r_detach']}"

    def test_boundary_threshold_low_k(self):
        """
        Verify behavior exactly at the lower threshold (k_est = 0.2).
        According to spec: "if k_est < 0.2", so 0.2 should NOT trigger the decrease.
        """
        k_est_boundary = 0.2
        weights = self.scheduler.get_reward_weights(k_est_boundary, self.base_weights)
        
        # At exactly 0.2, no decrease should happen (condition is strictly < 0.2)
        assert weights['r_contact'] == self.base_weights['r_contact'], \
            f"Expected no decrease at k_est=0.2, got {weights['r_contact']}"

    def test_very_high_stiffness_scaling(self):
        """
        Verify that extremely high k_est values result in significant detach reward increases.
        """
        k_est_very_high = 5.0
        weights = self.scheduler.get_reward_weights(k_est_very_high, self.base_weights)
        
        # Should still be at least 20% increase
        expected_min_detach = self.base_weights['r_detach'] * 1.20
        assert weights['r_detach'] >= expected_min_detach, \
            f"Expected r_detach >= {expected_min_detach} for k_est={k_est_very_high}, got {weights['r_detach']}"
        
        # Verify it's a reasonable multiplier (not exploding to infinity)
        assert weights['r_detach'] < 10.0, \
            f"r_detach seems unreasonably high: {weights['r_detach']} for k_est={k_est_very_high}"

    def test_very_low_stiffness_scaling(self):
        """
        Verify that extremely low k_est values result in significant contact reward decreases.
        """
        k_est_very_low = 0.01
        weights = self.scheduler.get_reward_weights(k_est_very_low, self.base_weights)
        
        # Should be at most 85% of base (15% decrease)
        expected_max_contact = self.base_weights['r_contact'] * 0.85
        assert weights['r_contact'] <= expected_max_contact, \
            f"Expected r_contact <= {expected_max_contact} for k_est={k_est_very_low}, got {weights['r_contact']}"
        
        # Verify it doesn't go to zero or negative
        assert weights['r_contact'] > 0.0, \
            f"r_contact should be positive: {weights['r_contact']} for k_est={k_est_very_low}"

    def test_zero_stiffness_handling(self):
        """
        Verify behavior when k_est is exactly 0.0 (no contact/stiction).
        """
        k_est_zero = 0.0
        weights = self.scheduler.get_reward_weights(k_est_zero, self.base_weights)
        
        # Should trigger the low stiffness logic (0.0 < 0.2)
        expected_max_contact = self.base_weights['r_contact'] * 0.85
        assert weights['r_contact'] <= expected_max_contact, \
            f"Expected r_contact <= {expected_max_contact} for k_est={k_est_zero}, got {weights['r_contact']}"

    def test_negative_stiffness_handling(self):
        """
        Verify behavior with negative k_est (should be rare but handled gracefully).
        """
        k_est_negative = -0.5
        weights = self.scheduler.get_reward_weights(k_est_negative, self.base_weights)
        
        # Should trigger the low stiffness logic (-0.5 < 0.2)
        expected_max_contact = self.base_weights['r_contact'] * 0.85
        assert weights['r_contact'] <= expected_max_contact, \
            f"Expected r_contact <= {expected_max_contact} for k_est={k_est_negative}, got {weights['r_contact']}"
        
        # Ensure weights remain positive
        assert weights['r_contact'] > 0.0 and weights['r_detach'] > 0.0, \
            "Reward weights should remain positive even for negative k_est"

    def test_custom_base_weights(self):
        """
        Verify that the scheduler works correctly with custom base weights.
        """
        custom_base = {
            'r_contact': 2.0,
            'r_detach': 0.5,
            'r_smooth': 1.0
        }
        
        # Test high stiffness
        k_est_high = 2.0
        weights_high = self.scheduler.get_reward_weights(k_est_high, custom_base)
        expected_detach_high = custom_base['r_detach'] * 1.20  # 0.5 * 1.2 = 0.6
        assert weights_high['r_detach'] >= expected_detach_high, \
            f"Expected r_detach >= {expected_detach_high} with custom base, got {weights_high['r_detach']}"
        
        # Test low stiffness
        k_est_low = 0.1
        weights_low = self.scheduler.get_reward_weights(k_est_low, custom_base)
        expected_contact_low = custom_base['r_contact'] * 0.85  # 2.0 * 0.85 = 1.7
        assert weights_low['r_contact'] <= expected_contact_low, \
            f"Expected r_contact <= {expected_contact_low} with custom base, got {weights_low['r_contact']}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])