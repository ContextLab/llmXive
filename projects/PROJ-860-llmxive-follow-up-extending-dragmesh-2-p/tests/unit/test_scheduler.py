"""
Unit tests for AdaptiveRewardScheduler logic.

Verifies weight scaling logic with explicit predefined thresholds:
- If k_est > 1.0, increase r_detach by >= 20%
- If k_est < 0.2, decrease r_contact by <= 15%
"""
import pytest
import sys
import os
import numpy as np

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from scheduler import AdaptiveRewardScheduler


class TestAdaptiveRewardScheduler:
    """Tests for AdaptiveRewardScheduler logic."""

    def test_default_weights_initialization(self):
        """Test that default weights are initialized correctly."""
        scheduler = AdaptiveRewardScheduler()
        assert scheduler.r_contact == 1.0
        assert scheduler.r_detach == 1.0
        assert scheduler.k_est == 1.0  # Default neutral value

    def test_high_k_est_increases_detach_reward(self):
        """
        Test that when k_est > 1.0, r_detach increases by >= 20%.
        
        According to FR-002: if k_est > 1.0, increase r_detach by >= 20%
        """
        scheduler = AdaptiveRewardScheduler()
        
        # Test with k_est = 1.5 (50% above threshold)
        scheduler.update_weights(k_est=1.5)
        
        # Expected: r_detach should increase by at least 20%
        expected_min_increase = 1.0 * 1.20  # 20% increase
        assert scheduler.r_detach >= expected_min_increase, \
            f"Expected r_detach >= {expected_min_increase}, got {scheduler.r_detach}"
        
        # r_contact should remain unchanged or decrease slightly (not specified for high k_est)
        # We expect it to stay at baseline or adjust based on other logic
        assert scheduler.r_contact <= 1.0  # Should not increase

    def test_high_k_est_edge_case(self):
        """Test edge case where k_est is exactly 1.0."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=1.0)
        
        # At exactly 1.0, no increase should occur (threshold is > 1.0)
        assert scheduler.r_detach == 1.0, \
            "r_detach should not increase when k_est is exactly 1.0"

    def test_low_k_est_decreases_contact_reward(self):
        """
        Test that when k_est < 0.2, r_contact decreases by <= 15%.
        
        According to FR-002: if k_est < 0.2, decrease r_contact by <= 15%
        """
        scheduler = AdaptiveRewardScheduler()
        
        # Test with k_est = 0.1 (below threshold)
        scheduler.update_weights(k_est=0.1)
        
        # Expected: r_contact should decrease by at most 15%
        # So it should be >= 85% of original
        expected_min_value = 1.0 * 0.85  # 15% decrease
        assert scheduler.r_contact >= expected_min_value, \
            f"Expected r_contact >= {expected_min_value}, got {scheduler.r_contact}"
        
        # Also verify it actually decreased
        assert scheduler.r_contact < 1.0, \
            "r_contact should decrease when k_est < 0.2"

    def test_low_k_est_edge_case(self):
        """Test edge case where k_est is exactly 0.2."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=0.2)
        
        # At exactly 0.2, no decrease should occur (threshold is < 0.2)
        assert scheduler.r_contact == 1.0, \
            "r_contact should not decrease when k_est is exactly 0.2"

    def test_moderate_k_est_no_change(self):
        """Test that moderate k_est values (0.2 <= k_est <= 1.0) don't trigger adjustments."""
        scheduler = AdaptiveRewardScheduler()
        
        # Test with k_est = 0.5 (moderate range)
        scheduler.update_weights(k_est=0.5)
        
        # No adjustments should occur
        assert scheduler.r_contact == 1.0, \
            "r_contact should not change for moderate k_est"
        assert scheduler.r_detach == 1.0, \
            "r_detach should not change for moderate k_est"

    def test_extreme_high_k_est(self):
        """Test with very high k_est value."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=3.0)
        
        # Should still follow the >= 20% increase rule
        assert scheduler.r_detach >= 1.20, \
            f"Expected r_detach >= 1.20 for high k_est, got {scheduler.r_detach}"

    def test_extreme_low_k_est(self):
        """Test with very low k_est value."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=0.05)
        
        # Should still follow the <= 15% decrease rule
        assert scheduler.r_contact >= 0.85, \
            f"Expected r_contact >= 0.85 for low k_est, got {scheduler.r_contact}"
        assert scheduler.r_contact < 1.0, \
            "r_contact should decrease for very low k_est"

    def test_multiple_updates_accumulate(self):
        """Test that multiple updates to k_est properly adjust weights."""
        scheduler = AdaptiveRewardScheduler()
        
        # First update: high k_est
        scheduler.update_weights(k_est=1.5)
        first_detach = scheduler.r_detach
        
        # Second update: low k_est
        scheduler.update_weights(k_est=0.1)
        
        # r_detach should have been set based on last update (low k_est doesn't affect it)
        # r_contact should have been decreased
        assert scheduler.r_contact < 1.0, \
            "r_contact should decrease after low k_est update"
        
        # Verify the detach reward was reset appropriately
        # (implementation dependent, but should not keep high value from previous)
        assert scheduler.r_detach <= first_detach, \
            "r_detach should not exceed previous high value after low k_est update"

    def test_k_est_zero_handling(self):
        """Test handling of k_est = 0 (edge case)."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=0.0)
        
        # Should trigger low k_est logic
        assert scheduler.r_contact < 1.0, \
            "r_contact should decrease for k_est = 0"
        assert scheduler.r_contact >= 0.85, \
            "r_contact decrease should be <= 15%"

    def test_k_est_very_high(self):
        """Test handling of extremely high k_est."""
        scheduler = AdaptiveRewardScheduler()
        scheduler.update_weights(k_est=10.0)
        
        # Should trigger high k_est logic
        assert scheduler.r_detach >= 1.20, \
            "r_detach should increase by >= 20% for very high k_est"

    def test_weight_bounds(self):
        """Test that weights stay within reasonable bounds."""
        scheduler = AdaptiveRewardScheduler()
        
        # Test various k_est values
        test_values = [0.0, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 5.0, 10.0]
        
        for k in test_values:
            scheduler.update_weights(k_est=k)
            
            # Weights should be positive
            assert scheduler.r_contact > 0, f"r_contact should be positive for k_est={k}"
            assert scheduler.r_detach > 0, f"r_detach should be positive for k_est={k}"
            
            # Reasonable upper bounds (implementation dependent, but should be bounded)
            assert scheduler.r_contact <= 2.0, \
                f"r_contact should not exceed 2.0 for k_est={k}"
            assert scheduler.r_detach <= 2.0, \
                f"r_detach should not exceed 2.0 for k_est={k}"

    def test_scheduler_state_persistence(self):
        """Test that scheduler maintains state between updates."""
        scheduler = AdaptiveRewardScheduler()
        
        # Set initial state
        scheduler.update_weights(k_est=1.5)
        initial_detach = scheduler.r_detach
        initial_contact = scheduler.r_contact
        
        # Create new scheduler and verify default state
        scheduler2 = AdaptiveRewardScheduler()
        assert scheduler2.r_detach == 1.0
        assert scheduler2.r_contact == 1.0
        
        # Verify first scheduler still has updated state
        assert scheduler.r_detach == initial_detach
        assert scheduler.r_contact == initial_contact

    def test_update_weights_returns_weights(self):
        """Test that update_weights returns the updated weights."""
        scheduler = AdaptiveRewardScheduler()
        result = scheduler.update_weights(k_est=1.5)
        
        # Should return a tuple or dict with the weights
        assert result is not None, "update_weights should return the weights"
        
        # Check if it returns a tuple (r_contact, r_detach)
        if isinstance(result, tuple):
            assert len(result) == 2
            assert result[0] == scheduler.r_contact
            assert result[1] == scheduler.r_detach
        # Or if it returns a dict
        elif isinstance(result, dict):
            assert 'r_contact' in result
            assert 'r_detach' in result
            assert result['r_contact'] == scheduler.r_contact
            assert result['r_detach'] == scheduler.r_detach

    def test_realistic_friction_scenarios(self):
        """Test with realistic friction coefficient scenarios."""
        scheduler = AdaptiveRewardScheduler()
        
        # Scenario 1: High friction object (k_est > 1.0)
        scheduler.update_weights(k_est=1.8)
        assert scheduler.r_detach >= 1.20, \
            "High friction should increase detach reward"
        
        # Scenario 2: Low friction object (k_est < 0.2)
        scheduler.update_weights(k_est=0.15)
        assert scheduler.r_contact < 1.0, \
            "Low friction should decrease contact reward"
        assert scheduler.r_contact >= 0.85, \
            "Low friction decrease should be <= 15%"
        
        # Scenario 3: Normal friction (0.2 <= k_est <= 1.0)
        scheduler.update_weights(k_est=0.6)
        assert scheduler.r_contact == 1.0, \
            "Normal friction should not change contact reward"
        assert scheduler.r_detach == 1.0, \
            "Normal friction should not change detach reward"

    def test_threshold_precision(self):
        """Test precision of threshold boundaries."""
        scheduler = AdaptiveRewardScheduler()
        
        # Test values very close to thresholds
        test_cases = [
            (0.19999, True, False),   # Just below 0.2 - should decrease contact
            (0.20001, False, False),  # Just above 0.2 - no change
            (0.99999, False, False),  # Just below 1.0 - no change
            (1.00001, False, True),   # Just above 1.0 - should increase detach
        ]
        
        for k_est, should_decrease_contact, should_increase_detach in test_cases:
            scheduler.update_weights(k_est=k_est)
            
            if should_decrease_contact:
                assert scheduler.r_contact < 1.0, \
                    f"r_contact should decrease for k_est={k_est}"
            else:
                assert scheduler.r_contact == 1.0, \
                    f"r_contact should not change for k_est={k_est}"
            
            if should_increase_detach:
                assert scheduler.r_detach >= 1.20, \
                    f"r_detach should increase for k_est={k_est}"
            else:
                assert scheduler.r_detach == 1.0, \
                    f"r_detach should not change for k_est={k_est}"