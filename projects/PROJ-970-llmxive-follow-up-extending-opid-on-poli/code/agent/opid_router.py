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
    seed: Optional[int] = None
    log_level: str = "INFO"

class OPIDRouter:
    """
    OPID Router implementing critical-first routing logic.
    
    Uses a Bernoulli trial with p = 1 - threshold to decide whether to
    inject hindsight skill distillation signals.
    """
    
    def __init__(self, config: OPIDRouterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set seed for reproducibility if provided
        if config.seed is not None:
            set_seed(config.seed)
            self.logger.info(f"OPIDRouter initialized with seed: {config.seed}")
        
        self.logger.info(f"OPIDRouter initialized with routing_threshold: {config.routing_threshold}")

    def should_inject_skill(self) -> bool:
        """
        Perform Bernoulli trial to decide if skill injection should occur.
        
        Probability of injection p = 1 - routing_threshold.
        - If threshold is 0.0, p=1.0 (always inject)
        - If threshold is 1.0, p=0.0 (never inject)
        
        Returns:
            bool: True if skill injection should occur, False otherwise.
        """
        injection_prob = 1.0 - self.config.routing_threshold
        
        # Use numpy for consistent random number generation with seed
        # Ensure we handle edge cases where probability is exactly 0 or 1
        if injection_prob <= 0.0:
            result = False
        elif injection_prob >= 1.0:
            result = True
        else:
            result = np.random.random() < injection_prob
        
        self.logger.debug(
            f"Routing decision: threshold={self.config.routing_threshold}, "
            f"injection_prob={injection_prob:.4f}, result={result}"
        )
        
        return result

    def route(self, state: Dict[str, Any], action_space: List[Any]) -> Dict[str, Any]:
        """
        Route action selection based on critical-first logic.
        
        Args:
            state: Current state dictionary
            action_space: List of available actions
            
        Returns:
            Dict containing routing decision and metadata
        """
        inject_skill = self.should_inject_skill()
        
        result = {
            "inject_skill": inject_skill,
            "routing_threshold": self.config.routing_threshold,
            "state_hash": hash(str(state)) % 1000000,  # For logging purposes
            "action_space_size": len(action_space)
        }
        
        if inject_skill:
            self.logger.info(
                f"Skill injection triggered (threshold={self.config.routing_threshold})"
            )
        else:
            self.logger.debug(
                f"Skill injection suppressed (threshold={self.config.routing_threshold})"
            )
        
        return result

def main():
    """Main entry point for testing the OPIDRouter."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with different thresholds
    test_cases = [
        OPIDRouterConfig(routing_threshold=0.0, seed=42),  # Always inject
        OPIDRouterConfig(routing_threshold=0.5, seed=42),  # 50% chance
        OPIDRouterConfig(routing_threshold=1.0, seed=42),  # Never inject
    ]
    
    for config in test_cases:
        print(f"\nTesting with threshold={config.routing_threshold}")
        router = OPIDRouter(config)
        
        # Run multiple trials to verify probability distribution
        trials = 1000
        inject_count = 0
        for _ in range(trials):
            if router.should_inject_skill():
                inject_count += 1
        
        actual_prob = inject_count / trials
        expected_prob = 1.0 - config.routing_threshold
        
        print(f"  Expected injection probability: {expected_prob:.2f}")
        print(f"  Actual injection rate: {actual_prob:.2f} ({inject_count}/{trials})")
        
        # Verify logic matches specification
        assert abs(actual_prob - expected_prob) < 0.05, \
            f"Probability mismatch: expected {expected_prob}, got {actual_prob}"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    main()