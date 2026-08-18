"""
AdaptiveRewardScheduler implementation for virtual tactile adaptation.

Maps estimated friction coefficient (k_est) to reward weights with explicit
logic for adjusting contact and detach rewards based on friction levels.
"""
import numpy as np
from typing import Dict, Any

class AdaptiveRewardScheduler:
    """
    Adjusts reward weights based on estimated friction coefficient k_est.
    
    FR-002 Implementation:
    - If k_est > 1.0: increase r_detach by >= 20%
    - If k_est < 0.2: decrease r_contact by <= 15%
    """
    
    def __init__(
        self,
        base_contact_weight: float = 1.0,
        base_detach_weight: float = 1.0,
        high_friction_threshold: float = 1.0,
        low_friction_threshold: float = 0.2,
        high_friction_increase: float = 0.20,
        low_friction_decrease: float = 0.15
    ):
        """
        Initialize the adaptive reward scheduler.
        
        Args:
            base_contact_weight: Base weight for contact reward
            base_detach_weight: Base weight for detach reward
            high_friction_threshold: k_est threshold for high friction
            low_friction_threshold: k_est threshold for low friction
            high_friction_increase: Minimum increase for r_detach when k_est > threshold
            low_friction_decrease: Maximum decrease for r_contact when k_est < threshold
        """
        self.base_contact_weight = base_contact_weight
        self.base_detach_weight = base_detach_weight
        self.high_friction_threshold = high_friction_threshold
        self.low_friction_threshold = low_friction_threshold
        self.high_friction_increase = high_friction_increase
        self.low_friction_decrease = low_friction_decrease
        
        self.current_k_est = None
        self.current_weights = self.get_initial_weights()
    
    def get_initial_weights(self) -> Dict[str, float]:
        """Return initial reward weights (no adaptation)."""
        return {
            'contact': self.base_contact_weight,
            'detach': self.base_detach_weight
        }
    
    def update(self, k_est: float) -> Dict[str, float]:
        """
        Update reward weights based on estimated friction coefficient.
        
        Args:
            k_est: Estimated friction coefficient
            
        Returns:
            dict: Updated reward weights with 'contact' and 'detach' keys
        """
        self.current_k_est = k_est
        weights = self.get_initial_weights()
        
        # Apply FR-002 logic
        if k_est > self.high_friction_threshold:
            # Increase detach reward by at least 20%
            weights['detach'] = self.base_detach_weight * (1.0 + self.high_friction_increase)
            # Optionally reduce contact reward slightly to encourage detachment
            weights['contact'] = self.base_contact_weight * (1.0 - 0.05)
            
        elif k_est < self.low_friction_threshold:
            # Decrease contact reward by at most 15%
            weights['contact'] = self.base_contact_weight * (1.0 - self.low_friction_decrease)
            # Maintain detach reward for low friction
            weights['detach'] = self.base_detach_weight
            
        else:
            # Normal friction range - use base weights
            weights['contact'] = self.base_contact_weight
            weights['detach'] = self.base_detach_weight
        
        self.current_weights = weights
        return weights
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get current reward weights.
        
        Returns:
            dict: Current reward weights
        """
        if self.current_weights is None:
            return self.get_initial_weights()
        return self.current_weights.copy()
    
    def get_k_est(self) -> float:
        """
        Get the last estimated friction coefficient.
        
        Returns:
            float: Last k_est value, or 0.0 if not yet computed
        """
        return self.current_k_est if self.current_k_est is not None else 0.0


if __name__ == "__main__":
    """
    Self-test block to verify FR-002 logic:
    - If k_est > 1.0, r_detach increases by >= 20%
    - If k_est < 0.2, r_contact decreases by <= 15%
    """
    import sys
    
    print("Running AdaptiveRewardScheduler self-test...")
    
    scheduler = AdaptiveRewardScheduler(
        base_contact_weight=1.0,
        base_detach_weight=1.0,
        high_friction_threshold=1.0,
        low_friction_threshold=0.2,
        high_friction_increase=0.20,
        low_friction_decrease=0.15
    )
    
    # Test 1: High friction (k_est > 1.0)
    print("\n--- Test 1: High Friction (k_est = 1.5) ---")
    k_est_high = 1.5
    weights_high = scheduler.update(k_est_high)
    print(f"k_est: {k_est_high}")
    print(f"Resulting weights: {weights_high}")
    
    detach_increase = (weights_high['detach'] - scheduler.base_detach_weight) / scheduler.base_detach_weight
    print(f"Detach increase: {detach_increase * 100:.2f}%")
    
    assert detach_increase >= 0.20, f"FR-002 Violation: Detach increase ({detach_increase:.2%}) is less than required 20%"
    print("✓ PASS: Detach reward increased by >= 20%")
    
    # Test 2: Low friction (k_est < 0.2)
    print("\n--- Test 2: Low Friction (k_est = 0.1) ---")
    k_est_low = 0.1
    weights_low = scheduler.update(k_est_low)
    print(f"k_est: {k_est_low}")
    print(f"Resulting weights: {weights_low}")
    
    contact_decrease = (scheduler.base_contact_weight - weights_low['contact']) / scheduler.base_contact_weight
    print(f"Contact decrease: {contact_decrease * 100:.2f}%")
    
    assert contact_decrease <= 0.15, f"FR-002 Violation: Contact decrease ({contact_decrease:.2%}) exceeds maximum allowed 15%"
    # Also verify it is a decrease (non-zero)
    assert contact_decrease > 0, "Contact reward should decrease for low friction"
    print("✓ PASS: Contact reward decreased by <= 15%")
    
    # Test 3: Normal friction (0.2 <= k_est <= 1.0)
    print("\n--- Test 3: Normal Friction (k_est = 0.5) ---")
    k_est_normal = 0.5
    weights_normal = scheduler.update(k_est_normal)
    print(f"k_est: {k_est_normal}")
    print(f"Resulting weights: {weights_normal}")
    
    assert weights_normal['contact'] == scheduler.base_contact_weight, "Contact weight should be base value"
    assert weights_normal['detach'] == scheduler.base_detach_weight, "Detach weight should be base value"
    print("✓ PASS: Weights remain at base values")
    
    print("\n--- All Self-Tests Passed ---")
    print("FR-002 logic verified successfully.")
    sys.exit(0)
