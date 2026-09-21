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

class OPIDRouter:
    """
    OPID Router implementing critical-first routing logic.
    
    Controls hindsight skill injection density based on a tunable threshold.
    """
    
    def __init__(self, config: Optional[OPIDRouterConfig] = None):
        if config is None:
            config = OPIDRouterConfig()
        
        self.routing_threshold = config.routing_threshold
        set_seed(config.seed)
        self.logger = logging.getLogger(__name__)
        
        # Validate threshold range
        if not (0.0 <= self.routing_threshold <= 1.0):
            raise ValueError(f"routing_threshold must be between 0.0 and 1.0, got {self.routing_threshold}")

    def should_inject(self, state: Dict[str, Any]) -> bool:
        """
        Determine if a skill signal should be injected for the current state.
        
        Implements Bernoulli trial with p = 1 - threshold.
        Returns True if injection should occur, False otherwise.
        
        Args:
            state: Current environment state dictionary
            
        Returns:
            bool: True if skill signal should be injected, False to suppress
        """
        # Bernoulli trial: p = 1 - threshold
        # If threshold is 0.0 -> p = 1.0 (always inject)
        # If threshold is 1.0 -> p = 0.0 (never inject)
        p_inject = 1.0 - self.routing_threshold
        result = random.random() < p_inject
        
        if not result:
            # Suppress skill signal: policy acts as baseline
            self.logger.debug(f"Suppressing skill signal (threshold={self.routing_threshold}, p_inject={p_inject:.2f})")
        
        return result

    def inject_skill_signal(self, state: Dict[str, Any], policy_logits: List[float]) -> List[float]:
        """
        Inject a skill signal by modifying policy logits.
        
        Adds a constant advantage to the goal-directed action.
        
        Args:
            state: Current environment state
            policy_logits: Raw logits from the baseline policy
            
        Returns:
            List[float]: Modified logits with skill signal injected
        """
        if not self.should_inject(state):
            # Suppress skill signal: return baseline policy unchanged
            return policy_logits
        
        # Simulate log-probability shift (add constant advantage to goal action)
        # For demonstration, assume the last action index is the goal-directed action
        modified_logits = policy_logits.copy()
        goal_action_idx = len(modified_logits) - 1
        advantage = 2.0  # Fixed advantage for skill injection
        modified_logits[goal_action_idx] += advantage
        
        self.logger.debug(f"Injected skill signal: added advantage {advantage} to action {goal_action_idx}")
        return modified_logits

    def get_policy_action(self, state: Dict[str, Any], policy_logits: List[float]) -> Tuple[int, List[float]]:
        """
        Get the selected action, potentially with skill signal injection.
        
        This is the main entry point for the policy decision process.
        
        Args:
            state: Current environment state
            policy_logits: Raw logits from the baseline policy
            
        Returns:
            Tuple[int, List[float]]: (selected_action_index, final_logits_used)
        """
        # Check if we should inject skill signal
        if self.should_inject(state):
            # Inject skill signal and get modified logits
            final_logits = self.inject_skill_signal(state, policy_logits)
            # Select action based on modified logits (softmax sampling)
            probs = np.exp(final_logits) / np.sum(np.exp(final_logits))
            selected_action = np.random.choice(len(probs), p=probs)
        else:
            # Suppress skill signal: use baseline policy as-is
            final_logits = policy_logits
            probs = np.exp(policy_logits) / np.sum(np.exp(policy_logits))
            selected_action = np.random.choice(len(probs), p=probs)
        
        return selected_action, final_logits

def main():
    """Main function to demonstrate OPIDRouter functionality."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with different thresholds
    for threshold in [0.0, 0.5, 1.0]:
        print(f"\n--- Testing with threshold={threshold} ---")
        config = OPIDRouterConfig(routing_threshold=threshold, seed=42)
        router = OPIDRouter(config)
        
        # Simulate a few states
        for i in range(5):
            state = {"step": i, "location": f"node_{i}"}
            should_inject = router.should_inject(state)
            print(f"State {i}: should_inject={should_inject}")

if __name__ == "__main__":
    main()