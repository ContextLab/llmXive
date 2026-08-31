"""
Adaptive Reward Scheduler Module.

Implements the AdaptiveRewardScheduler class to map the estimated friction coefficient
(k_est) to reward weights for the training loop, dynamically adjusting detachment
and contact penalties based on real-time tactile feedback.
"""

import numpy as np
from typing import Dict, Any, Tuple


class AdaptiveRewardScheduler:
    """
    Dynamically adjusts reward weights based on the estimated friction coefficient k_est.

    Logic (FR-002):
      - If k_est > 1.0 (High Friction): Increase r_detach by >= 20% to encourage
        safer, more controlled detachment to prevent slipping.
      - If k_est < 0.2 (Low Friction): Decrease r_contact by <= 15% to reduce
        the penalty for light contact, allowing more exploration.
      - Otherwise: Use base weights.
    """

    def __init__(
        self,
        base_r_detach: float = 1.0,
        base_r_contact: float = 1.0,
        high_k_threshold: float = 1.0,
        low_k_threshold: float = 0.2,
        high_k_increase_factor: float = 1.25,  # 25% increase (>= 20%)
        low_k_decrease_factor: float = 0.85    # 15% decrease (<= 15%)
    ):
        """
        Initialize the scheduler.

        Args:
            base_r_detach: Base reward weight for detachment.
            base_r_contact: Base reward weight for contact.
            high_k_threshold: Threshold above which high-friction logic applies.
            low_k_threshold: Threshold below which low-friction logic applies.
            high_k_increase_factor: Multiplier for r_detach when k_est is high.
            low_k_decrease_factor: Multiplier for r_contact when k_est is low.
        """
        self.base_r_detach = base_r_detach
        self.base_r_contact = base_r_contact
        self.high_k_threshold = high_k_threshold
        self.low_k_threshold = low_k_threshold
        self.high_k_increase_factor = high_k_increase_factor
        self.low_k_decrease_factor = low_k_decrease_factor

        # Validation
        if self.high_k_increase_factor < 1.2:
            raise ValueError("high_k_increase_factor must be >= 1.2 (20% increase)")
        if self.low_k_decrease_factor > 0.85:
            raise ValueError("low_k_decrease_factor must be <= 0.85 (15% decrease)")

    def get_reward_weights(self, k_est: float) -> Tuple[float, float]:
        """
        Calculate the current reward weights based on k_est.

        Args:
            k_est: The current estimated friction coefficient.

        Returns:
            A tuple (r_detach, r_contact) with adjusted weights.
        """
        if not np.isfinite(k_est):
            # Fallback to base weights if k_est is invalid
            return self.base_r_detach, self.base_r_contact

        r_detach = self.base_r_detach
        r_contact = self.base_r_contact

        if k_est > self.high_k_threshold:
            # High friction: Increase detachment penalty
            r_detach = self.base_r_detach * self.high_k_increase_factor
        elif k_est < self.low_k_threshold:
            # Low friction: Decrease contact penalty
            r_contact = self.base_r_contact * self.low_k_decrease_factor

        return r_detach, r_contact

    def get_adjustment_log(self, k_est: float) -> Dict[str, Any]:
        """
        Get a detailed log of the adjustment logic for the current k_est.

        Args:
            k_est: The current estimated friction coefficient.

        Returns:
            Dictionary with k_est, decision logic, and resulting weights.
        """
        r_detach, r_contact = self.get_reward_weights(k_est)
        
        decision = "standard"
        if k_est > self.high_k_threshold:
            decision = "high_friction_adjustment"
        elif k_est < self.low_k_threshold:
            decision = "low_friction_adjustment"

        return {
            "k_est": k_est,
            "decision": decision,
            "r_detach": r_detach,
            "r_contact": r_contact,
            "base_r_detach": self.base_r_detach,
            "base_r_contact": self.base_r_contact,
            "thresholds": {
                "high": self.high_k_threshold,
                "low": self.low_k_threshold
            }
        }

    # Self-test block for verification (FR-002 compliance)
    if __name__ == "__main__":
        import sys
        print("Running AdaptiveRewardScheduler self-test...")
        
        scheduler = AdaptiveRewardScheduler()
        
        # Test 1: High friction (k_est = 1.5)
        k_high = 1.5
        r_d_high, r_c_high = scheduler.get_reward_weights(k_high)
        expected_d_high = scheduler.base_r_detach * 1.25
        assert abs(r_d_high - expected_d_high) < 1e-6, f"High friction r_detach mismatch: {r_d_high} != {expected_d_high}"
        assert r_d_high >= scheduler.base_r_detach * 1.20, "High friction increase must be >= 20%"
        print(f"[PASS] High friction (k={k_high}): r_detach={r_d_high:.2f} (>= 1.20x base)")

        # Test 2: Low friction (k_est = 0.1)
        k_low = 0.1
        r_d_low, r_c_low = scheduler.get_reward_weights(k_low)
        expected_c_low = scheduler.base_r_contact * 0.85
        assert abs(r_c_low - expected_c_low) < 1e-6, f"Low friction r_contact mismatch: {r_c_low} != {expected_c_low}"
        assert r_c_low <= scheduler.base_r_contact * 0.85, "Low friction decrease must be <= 15%"
        print(f"[PASS] Low friction (k={k_low}): r_contact={r_c_low:.2f} (<= 0.85x base)")

        # Test 3: Standard (k_est = 0.5)
        k_std = 0.5
        r_d_std, r_c_std = scheduler.get_reward_weights(k_std)
        assert abs(r_d_std - scheduler.base_r_detach) < 1e-6, "Standard r_detach should be base"
        assert abs(r_c_std - scheduler.base_r_contact) < 1e-6, "Standard r_contact should be base"
        print(f"[PASS] Standard (k={k_std}): No adjustment applied")

        print("All self-tests passed.")