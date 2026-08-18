"""
Unit tests for AdaptiveRewardScheduler logic (FR-002).

Verifies:
- If k_est > 1.0, r_detach increases by >= 20%
- If k_est < 0.2, r_contact decreases by <= 15%
"""
import pytest
import sys
import os
import numpy as np

# Add code directory to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from scheduler import AdaptiveRewardScheduler


class TestAdaptiveRewardScheduler:
    """Test suite for AdaptiveRewardScheduler FR-002 compliance."""
    
    @pytest.fixture
    def scheduler(self):
        """Create a standard scheduler instance."""
        return AdaptiveRewardScheduler(
            base_contact_weight=1.0,
            base_detach_weight=1.0,
            high_friction_threshold=1.0,
            low_friction_threshold=0.2,
            high_friction_increase=0.20,
            low_friction_decrease=0.15
        )
    
    def test_high_friction_detach_increase(self, scheduler):
        """
        Verify that if k_est > 1.0, r_detach increases by >= 20%.
        """
        k_est = 1.5  # Clearly above threshold
        weights = scheduler.update(k_est)
        
        detach_increase = (weights['detach'] - scheduler.base_detach_weight) / scheduler.base_detach_weight
        
        # Assert >= 20% increase
        assert detach_increase >= 0.20, (
            f"FR-002 Violation: Detach increase ({detach_increase:.2%}) "
            f"is less than required 20% for k_est={k_est}"
        )
        
        # Verify the actual value matches expected (1.20)
        assert np.isclose(weights['detach'], 1.20), \
            f"Expected detach weight 1.20, got {weights['detach']}"
    
    def test_high_friction_contact_reduction(self, scheduler):
        """
        Verify that for high friction, contact weight is slightly reduced.
        """
        k_est = 2.0
        weights = scheduler.update(k_est)
        
        # Expect 5% reduction based on implementation
        assert np.isclose(weights['contact'], 0.95), \
            f"Expected contact weight 0.95, got {weights['contact']}"
    
    def test_low_friction_contact_decrease(self, scheduler):
        """
        Verify that if k_est < 0.2, r_contact decreases by <= 15%.
        """
        k_est = 0.1  # Clearly below threshold
        weights = scheduler.update(k_est)
        
        contact_decrease = (scheduler.base_contact_weight - weights['contact']) / scheduler.base_contact_weight
        
        # Assert <= 15% decrease
        assert contact_decrease <= 0.15, (
            f"FR-002 Violation: Contact decrease ({contact_decrease:.2%}) "
            f"exceeds maximum allowed 15% for k_est={k_est}"
        )
        
        # Assert it actually decreased (not zero)
        assert contact_decrease > 0, \
            "Contact weight should decrease for low friction"
        
        # Verify the actual value matches expected (0.85)
        assert np.isclose(weights['contact'], 0.85), \
            f"Expected contact weight 0.85, got {weights['contact']}"
    
    def test_low_friction_detach_unchanged(self, scheduler):
        """
        Verify that for low friction, detach weight remains at base.
        """
        k_est = 0.05
        weights = scheduler.update(k_est)
        
        assert np.isclose(weights['detach'], scheduler.base_detach_weight), \
            f"Detach weight should remain at base for low friction"
    
    def test_normal_friction_unchanged(self, scheduler):
        """
        Verify that for normal friction (0.2 <= k_est <= 1.0), weights are unchanged.
        """
        k_est = 0.5
        weights = scheduler.update(k_est)
        
        assert weights['contact'] == scheduler.base_contact_weight, \
            "Contact weight should be base value"
        assert weights['detach'] == scheduler.base_detach_weight, \
            "Detach weight should be base value"
    
    def test_boundary_high_friction(self, scheduler):
        """
        Test exact boundary k_est = 1.0 (should be normal, not high).
        """
        k_est = 1.0
        weights = scheduler.update(k_est)
        
        # At exactly 1.0, it falls into the 'else' (normal) case based on strict inequality
        assert weights['contact'] == scheduler.base_contact_weight
        assert weights['detach'] == scheduler.base_detach_weight
    
    def test_boundary_low_friction(self, scheduler):
        """
        Test exact boundary k_est = 0.2 (should be normal, not low).
        """
        k_est = 0.2
        weights = scheduler.update(k_est)
        
        # At exactly 0.2, it falls into the 'else' (normal) case based on strict inequality
        assert weights['contact'] == scheduler.base_contact_weight
        assert weights['detach'] == scheduler.base_detach_weight
    
    def test_get_k_est(self, scheduler):
        """Test retrieval of current k_est."""
        assert scheduler.get_k_est() == 0.0, "Initial k_est should be 0.0"
        
        scheduler.update(0.5)
        assert scheduler.get_k_est() == 0.5
        
        scheduler.update(1.5)
        assert scheduler.get_k_est() == 1.5
    
    def test_get_weights_initial(self, scheduler):
        """Test initial weights retrieval before update."""
        weights = scheduler.get_weights()
        assert weights['contact'] == 1.0
        assert weights['detach'] == 1.0
    
    def test_get_weights_after_update(self, scheduler):
        """Test weights retrieval after update."""
        scheduler.update(1.5)
        weights = scheduler.get_weights()
        assert weights['detach'] == 1.20
        assert weights['contact'] == 0.95