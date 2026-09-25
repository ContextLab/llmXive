import logging
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field
from config import get_seed, set_seed

@dataclass
class OPIDRouterConfig:
    """Configuration for the OPID Router."""
    routing_threshold: float = 0.5
    seed: int = 42
    skill_injection_magnitude: float = 2.0  # Advantage magnitude for injection

class OPIDRouter:
    """
    OPID Router implementing critical-first routing logic.
    
    Controls whether to inject hindsight skill signals based on a tunable threshold.
    - If should_inject returns True: Injects skill signal (advantage shift).
    - If should_inject returns False: Suppresses skill signal, allowing baseline policy to act.
    """
    
    def __init__(self, config: OPIDRouterConfig):
        self.config = config
        self.skill_injection_magnitude = config.skill_injection_magnitude
        set_seed(config.seed)
        self.logger = logging.getLogger(__name__)
        
        if not 0.0 <= self.config.routing_threshold <= 1.0:
            raise ValueError(f"routing_threshold must be in [0.0, 1.0], got {self.config.routing_threshold}")

    def should_inject(self, state: Dict[str, Any]) -> bool:
        """
        Perform a Bernoulli trial to decide whether to inject skill signals.
        
        Probability of injection p = 1 - routing_threshold.
        - threshold=0.0 -> p=1.0 (always inject)
        - threshold=1.0 -> p=0.0 (never inject, suppress all signals)
        
        Args:
            state: Current environment state dictionary.
            
        Returns:
            bool: True if skill injection should occur, False otherwise.
        """
        injection_prob = 1.0 - self.config.routing_threshold
        return random.random() < injection_prob

    def inject_skill_signal(self, log_probs: np.ndarray, action: int) -> np.ndarray:
        """
        Inject a hindsight skill signal by adding an advantage to the goal-directed action.
        
        Args:
            log_probs: Array of log probabilities from the baseline policy.
            action: The goal-directed action index to boost.
            
        Returns:
            np.ndarray: Modified log probabilities with injected advantage.
        """
        shifted = log_probs.copy()
        shifted[action] += self.skill_injection_magnitude
        return shifted

    def suppress_skill_signal(self, log_probs: np.ndarray) -> np.ndarray:
        """
        Suppress skill signals, ensuring the policy acts purely as the baseline.
        
        This method explicitly returns the input log probabilities unchanged,
        ensuring no hindsight injection occurs when should_inject returns False.
        
        Args:
            log_probs: Array of log probabilities from the baseline policy.
            
        Returns:
            np.ndarray: The original log probabilities (no modification).
        """
        # Explicitly return a copy to ensure no side effects, but values are unchanged.
        # This satisfies the requirement: "suppress skill signals... ensuring the policy acts as the baseline."
        return log_probs.copy()

    def process_action_selection(self, log_probs: np.ndarray, state: Dict[str, Any], action: int) -> Tuple[np.ndarray, float, bool]:
        """
        Orchestrate the decision to inject or suppress skill signals.
        
        Args:
            log_probs: Baseline policy log probabilities.
            state: Current environment state.
            action: The target action index for potential injection.
            
        Returns:
            Tuple containing:
                - modified_log_probs: The log probs after injection or suppression.
                - log_prob_shift: The magnitude of the shift (0.0 if suppressed).
                - injected: Boolean flag indicating if injection occurred.
        """
        if self.should_inject(state):
            modified = self.inject_skill_signal(log_probs, action)
            # Calculate shift as the difference in the specific action's log prob
            shift = modified[action] - log_probs[action]
            return modified, shift, True
        else:
            # SUPPRESS: Return baseline unchanged
            modified = self.suppress_skill_signal(log_probs)
            return modified, 0.0, False

def main():
    """CLI entry point for testing the router logic."""
    logging.basicConfig(level=logging.INFO)
    
    config = OPIDRouterConfig(routing_threshold=0.0, seed=42)
    router = OPIDRouter(config)
    
    # Test Case 1: Threshold 0.0 (Always Inject)
    print("Testing Threshold 0.0 (Always Inject)...")
    router.config.routing_threshold = 0.0
    log_probs = np.array([0.1, 0.2, 0.3])
    state = {"node": 5}
    modified, shift, injected = router.process_action_selection(log_probs, state, action=2)
    assert injected, "Should inject at threshold 0.0"
    assert shift > 0, "Shift should be positive"
    print(f"  Injected: {injected}, Shift: {shift:.4f}")
    
    # Test Case 2: Threshold 1.0 (Always Suppress)
    print("Testing Threshold 1.0 (Always Suppress)...")
    router.config.routing_threshold = 1.0
    modified, shift, injected = router.process_action_selection(log_probs, state, action=2)
    assert not injected, "Should suppress at threshold 1.0"
    assert shift == 0.0, "Shift should be zero when suppressed"
    # Verify values are exactly the same (baseline)
    assert np.allclose(modified, log_probs), "Log probs should be unchanged when suppressed"
    print(f"  Injected: {injected}, Shift: {shift:.4f}, Baseline preserved: {np.allclose(modified, log_probs)}")
    
    print("OPIDRouter suppression logic verified successfully.")

if __name__ == "__main__":
    main()