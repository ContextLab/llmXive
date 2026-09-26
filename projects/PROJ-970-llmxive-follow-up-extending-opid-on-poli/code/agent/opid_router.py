import logging
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field
from seed import get_seed, set_seed

@dataclass
class OPIDRouterConfig:
    """Configuration for the OPID Router."""
    routing_threshold: float = 0.5
    seed: Optional[int] = None
    injection_advantage: float = 1.0  # Advantage to add when injecting

class OPIDRouter:
    """
    OPID Router with tunable critical-first routing threshold.
    
    Controls hindsight skill injection density based on a threshold parameter (0 to 1).
    - threshold = 0: Always inject (Bernoulli p=1)
    - threshold = 1: Never inject (Bernoulli p=0)
    """
    
    def __init__(self, config: OPIDRouterConfig):
        self.config = config
        if config.seed is not None:
            set_seed(config.seed)
        
        self.logger = logging.getLogger(__name__)
        
        # Validate threshold
        if not 0.0 <= config.routing_threshold <= 1.0:
            raise ValueError(f"routing_threshold must be between 0.0 and 1.0, got {config.routing_threshold}")
    
    def should_inject(self, state: Any) -> bool:
        """
        Perform a Bernoulli trial to decide whether to inject skill signal.
        
        Probability of injection: p = 1 - threshold
        
        Args:
            state: Current state representation (unused in this basic implementation)
        
        Returns:
            True if skill signal should be injected, False otherwise.
        """
        # Probability of injection
        p_inject = 1.0 - self.config.routing_threshold
        
        # Bernoulli trial
        result = random.random() < p_inject
        
        if result:
            self.logger.debug(f"Skill injection triggered (p={p_inject:.2f})")
        else:
            self.logger.debug(f"Skill injection suppressed (p={p_inject:.2f})")
        
        return result
    
    def inject_skill_signal(self, log_probs: np.ndarray, action: int) -> np.ndarray:
        """
        Inject skill signal by adding advantage to the goal-directed action.
        
        Args:
            log_probs: Array of log-probabilities for actions
            action: The goal-directed action to boost
        
        Returns:
            Modified log-probabilities with injected signal
        """
        modified_log_probs = log_probs.copy()
        modified_log_probs[action] += self.config.injection_advantage
        return modified_log_probs
    
    def process_action_selection(
        self,
        log_probs: np.ndarray,
        state: Any,
        goal_action: int
    ) -> Tuple[np.ndarray, bool, float]:
        """
        Process action selection with conditional skill injection.
        
        This is the main entry point for the router. It decides whether to inject
        skill signals based on the threshold, and if not injecting, returns the
        baseline policy unchanged.
        
        Args:
            log_probs: Baseline policy log-probabilities
            state: Current state
            goal_action: The action that would be selected under skill injection
        
        Returns:
            Tuple of (modified_log_probs, injected, log_prob_shift)
            - modified_log_probs: The log-probs to use for action selection
            - injected: Whether injection occurred
            - log_prob_shift: The magnitude of shift (0.0 if not injected)
        """
        injected = self.should_inject(state)
        
        if injected:
            # Inject skill signal
            modified_log_probs = self.inject_skill_signal(log_probs, goal_action)
            log_prob_shift = self.config.injection_advantage
            self.logger.debug(f"Injected skill signal for action {goal_action}, shift={log_prob_shift}")
        else:
            # Suppress skill signals - policy acts as baseline
            # Return original log_probs unchanged
            modified_log_probs = log_probs
            log_prob_shift = 0.0
            self.logger.debug(f"Suppressed skill signal - using baseline policy")
        
        return modified_log_probs, injected, log_prob_shift

def main():
    """Main entry point for standalone testing of the OPIDRouter."""
    import sys
    sys.path.insert(0, 'code')
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with threshold = 0.5 (50% injection rate)
    config = OPIDRouterConfig(routing_threshold=0.5, seed=42)
    router = OPIDRouter(config)
    
    # Simulate some states and check injection decisions
    print(f"Testing OPIDRouter with threshold={config.routing_threshold}")
    print(f"Expected injection rate: {1.0 - config.routing_threshold:.2f}")
    
    injections = 0
    trials = 1000
    
    for i in range(trials):
        if router.should_inject(state=i):
            injections += 1
    
    actual_rate = injections / trials
    print(f"Actual injection rate over {trials} trials: {actual_rate:.2f}")
    
    # Test signal injection
    base_log_probs = np.log([0.1, 0.2, 0.3, 0.4])
    goal_action = 3
    modified, injected, shift = router.process_action_selection(base_log_probs, state=0, goal_action=goal_action)
    
    print(f"\nBaseline log_probs: {base_log_probs}")
    print(f"Modified log_probs: {modified}")
    print(f"Injected: {injected}")
    print(f"Log prob shift: {shift}")

if __name__ == "__main__":
    main()