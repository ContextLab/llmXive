"""
Adaptive Reward Scheduler for Virtual Tactile Zero-Shot Adaptation.

This module implements the AdaptiveRewardScheduler class which maps the estimated
virtual tactile stiffness (k_est) to dynamic reward weights for the training loop.

FR-002 Logic:
- If k_est > 1.0: Increase detach reward (r_detach) by >= 20%
- If k_est < 0.2: Decrease contact reward (r_contact) by <= 15%
"""

import numpy as np
from typing import Dict, Any, Tuple

class AdaptiveRewardScheduler:
    """
    Adjusts reward weights based on the estimated stiffness k_est.

    Attributes:
        base_r_detach (float): Base reward weight for detachment.
        base_r_contact (float): Base reward weight for contact maintenance.
        current_r_detach (float): Current active reward weight for detachment.
        current_r_contact (float): Current active reward weight for contact.
        k_est_high_threshold (float): Threshold for high stiffness (default 1.0).
        k_est_low_threshold (float): Threshold for low stiffness (default 0.2).
        increase_factor (float): Minimum increase factor for high stiffness (1.20 for 20%).
        decrease_factor (float): Maximum decrease factor for low stiffness (0.85 for 15%).
    """

    def __init__(
        self,
        base_r_detach: float = 1.0,
        base_r_contact: float = 1.0,
        k_est_high_threshold: float = 1.0,
        k_est_low_threshold: float = 0.2,
        min_increase_pct: float = 0.20,
        max_decrease_pct: float = 0.15
    ):
        """
        Initialize the scheduler with base reward weights.

        Args:
            base_r_detach: Base weight for the detachment reward term.
            base_r_contact: Base weight for the contact reward term.
            k_est_high_threshold: Stiffness value above which detach reward increases.
            k_est_low_threshold: Stiffness value below which contact reward decreases.
            min_increase_pct: Minimum percentage increase (e.g., 0.20 for 20%).
            max_decrease_pct: Maximum percentage decrease (e.g., 0.15 for 15%).
        """
        self.base_r_detach = base_r_detach
        self.base_r_contact = base_r_contact
        self.current_r_detach = base_r_detach
        self.current_r_contact = base_r_contact

        self.k_est_high_threshold = k_est_high_threshold
        self.k_est_low_threshold = k_est_low_threshold
        
        # Multipliers derived from percentages
        self.increase_multiplier = 1.0 + min_increase_pct
        self.decrease_multiplier = 1.0 - max_decrease_pct

    def update_weights(self, k_est: float) -> Dict[str, float]:
        """
        Update reward weights based on the current k_est value.

        Logic:
        - If k_est > 1.0: r_detach = base * (1 + >=20%)
        - If k_est < 0.2: r_contact = base * (1 - <=15%)
        - Otherwise: reset to base weights.

        Args:
            k_est: The estimated virtual tactile stiffness from the estimator.

        Returns:
            A dictionary containing the updated weights:
            {
                "r_detach": float,
                "r_contact": float,
                "k_est": float,
                "adjustment_reason": str
            }
        """
        # Ensure k_est is a float and non-negative
        k_val = float(k_est)
        if k_val < 0:
            k_val = 0.0

        adjustment_reason = "base"

        if k_val > self.k_est_high_threshold:
            # High stiffness: Increase detach reward by at least 20%
            # We use the minimum required increase to be conservative, 
            # but could scale further if needed.
            self.current_r_detach = self.base_r_detach * self.increase_multiplier
            self.current_r_contact = self.base_r_contact # Reset contact to base
            adjustment_reason = "high_stiffness_detach_bonus"
        
        elif k_val < self.k_est_low_threshold:
            # Low stiffness: Decrease contact reward by at most 15%
            self.current_r_detach = self.base_r_detach # Reset detach to base
            self.current_r_contact = self.base_r_contact * self.decrease_multiplier
            adjustment_reason = "low_stiffness_contact_penalty"
        
        else:
            # Normal range: Reset to base
            self.current_r_detach = self.base_r_detach
            self.current_r_contact = self.base_r_contact
            adjustment_reason = "normal_range"

        return {
            "r_detach": self.current_r_detach,
            "r_contact": self.current_r_contact,
            "k_est": k_val,
            "adjustment_reason": adjustment_reason
        }

    def get_current_weights(self) -> Tuple[float, float]:
        """
        Returns the currently active reward weights.

        Returns:
            Tuple of (r_detach, r_contact).
        """
        return self.current_r_detach, self.current_r_contact

    def reset(self):
        """Reset weights to base values."""
        self.current_r_detach = self.base_r_detach
        self.current_r_contact = self.base_r_contact


# Self-test block as required by T006 specification
if __name__ == "__main__":
    import sys
    import logging

    # Setup basic logging to see output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting AdaptiveRewardScheduler self-test...")

    scheduler = AdaptiveRewardScheduler(
        base_r_detach=1.0,
        base_r_contact=1.0,
        min_increase_pct=0.20,
        max_decrease_pct=0.15
    )

    # Test Case 1: High Stiffness (k_est > 1.0)
    # Spec: Increase r_detach by >= 20%
    test_k_high = 1.5
    result_high = scheduler.update_weights(test_k_high)
    
    logger.info(f"Test High Stiffness: k_est = {test_k_high}")
    logger.info(f"  Result: r_detach = {result_high['r_detach']}, r_contact = {result_high['r_contact']}")
    
    # Verification
    expected_min_detach = 1.0 * 1.20
    actual_detach = result_high['r_detach']
    
    assert actual_detach >= expected_min_detach, (
        f"FAILED: High stiffness adjustment too small. "
        f"Expected r_detach >= {expected_min_detach}, got {actual_detach}"
    )
    logger.info(f"  ASSERTION PASSED: r_detach ({actual_detach}) >= {expected_min_detach} (20% increase)")

    # Test Case 2: Low Stiffness (k_est < 0.2)
    # Spec: Decrease r_contact by <= 15% (meaning it should be reduced, but not more than 15%? 
    # The phrasing "decrease ... by <= 15%" usually implies a cap on the reduction, 
    # but in context of reward shaping, it typically means "apply a reduction of up to 15%".
    # However, the spec says "decrease r_contact by <= 15%". 
    # Interpretation: The reduction factor is (1 - 0.15) = 0.85. 
    # We verify that the new weight is <= 0.85 * base (if we interpret "by <= 15%" as "at least 15% reduction"?)
    # Actually, standard English: "Decrease by X" means New = Old * (1 - X).
    # "Decrease by <= 15%" is ambiguous. It could mean "The decrease amount is <= 15% of base".
    # Given the context of FR-002 (punishing contact in low friction), we want to reduce the weight.
    # Let's assume the intent is to apply a 15% reduction (factor 0.85).
    # The spec says "decrease r_contact by <= 15%". 
    # If we decrease by 15%, the new value is 0.85. 
    # If we decrease by 10%, the new value is 0.90. 
    # The constraint "by <= 15%" likely means the reduction should not exceed 15% (i.e., don't zero it out).
    # So we verify: new_value >= 0.85 * base (since a larger reduction means a smaller number).
    # Wait, if I decrease by 20%, that's > 15%. So I must ensure decrease <= 15%.
    # So: (base - new) / base <= 0.15  =>  new >= base * 0.85.
    
    test_k_low = 0.1
    scheduler.reset() # Reset to ensure base
    result_low = scheduler.update_weights(test_k_low)

    logger.info(f"Test Low Stiffness: k_est = {test_k_low}")
    logger.info(f"  Result: r_detach = {result_low['r_detach']}, r_contact = {result_low['r_contact']}")

    expected_max_contact = 1.0 * (1.0 - 0.15) # 0.85
    actual_contact = result_low['r_contact']

    # Check that the contact weight was decreased (it should be lower than base)
    assert actual_contact < 1.0, f"FAILED: r_contact should be decreased, got {actual_contact}"
    
    # Check that the decrease is not MORE than 15% (i.e. value is not less than 85% of base)
    # "Decrease by <= 15%" -> Reduction <= 0.15 * Base -> New >= 0.85 * Base
    assert actual_contact >= expected_max_contact, (
        f"FAILED: Contact reward decreased too much. "
        f"Expected r_contact >= {expected_max_contact} (max 15% decrease), got {actual_contact}"
    )
    logger.info(f"  ASSERTION PASSED: r_contact ({actual_contact}) >= {expected_max_contact} (max 15% decrease)")

    # Test Case 3: Normal Range
    test_k_mid = 0.5
    scheduler.reset()
    result_mid = scheduler.update_weights(test_k_mid)
    
    logger.info(f"Test Normal Range: k_est = {test_k_mid}")
    logger.info(f"  Result: r_detach = {result_mid['r_detach']}, r_contact = {result_mid['r_contact']}")
    
    assert result_mid['r_detach'] == 1.0, "FAILED: Normal range should reset detach"
    assert result_mid['r_contact'] == 1.0, "FAILED: Normal range should reset contact"
    logger.info(f"  ASSERTION PASSED: Weights reset to base values.")

    logger.info("All self-test assertions passed successfully.")
    sys.exit(0)