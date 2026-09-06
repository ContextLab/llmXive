import logging
import random
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field
from config import get_seed, set_seed

@dataclass
class OPIDRouterConfig:
    routing_threshold: float = 0.5
    seed: int = 42
    log_file: str = "data/processed/opid_router_logs.jsonl"

class OPIDRouter:
    """
    OPID Router with critical-first routing logic.
    Injects hindsight skill distillation signals based on a Bernoulli trial
    determined by the routing_threshold.
    """
    def __init__(self, config: OPIDRouterConfig):
        self.config = config
        self.logger = logging.getLogger("OPIDRouter")
        self.log_file = config.log_file
        
        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        set_seed(config.seed)
        self.rng = random.Random(config.seed)

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Append a log entry to the JSONL file."""
        import json
        with open(self.log_file, 'a') as f:
            record = {
                "event": event_type,
                "data": data
            }
            f.write(json.dumps(record) + '\n')

    def route(self, state: Any, baseline_action_probs: Dict[str, float], 
              skill_action_probs: Dict[str, float]) -> Tuple[str, Dict[str, float], Dict[str, float]]:
        """
        Determines whether to inject a skill signal based on the routing threshold.
        
        Args:
            state: Current environment state.
            baseline_action_probs: Log-probabilities or probs from baseline policy.
            skill_action_probs: Log-probabilities or probs from skill policy.
        
        Returns:
            Tuple of (selected_action, final_probs, log_shift_info)
        """
        # Bernoulli trial: p = 1 - threshold for injection
        inject_prob = 1.0 - self.config.routing_threshold
        should_inject = self.rng.random() < inject_prob

        final_probs = {}
        log_shift = 0.0
        
        if should_inject:
            # Inject skill signal (weighted combination or override)
            # For this implementation, we assume a simple mixture or override
            # Let's assume skill_action_probs are the target distribution if injected
            final_probs = skill_action_probs
            log_shift = self._calculate_log_prob_shift(baseline_action_probs, skill_action_probs)
            
            self._log_event("skill_injection", {
                "threshold": self.config.routing_threshold,
                "inject_prob": inject_prob,
                "log_shift": log_shift,
                "action_selected": max(skill_action_probs, key=skill_action_probs.get)
            })
        else:
            # Suppress skill signal, use baseline
            final_probs = baseline_action_probs
            log_shift = 0.0
            
            self._log_event("skill_suppression", {
                "threshold": self.config.routing_threshold,
                "inject_prob": inject_prob,
                "log_shift": log_shift,
                "action_selected": max(baseline_action_probs, key=baseline_action_probs.get)
            })

        # Calculate selected action
        selected_action = max(final_probs, key=final_probs.get)
        
        return selected_action, final_probs, {"log_shift": log_shift, "injected": should_inject}

    def _calculate_log_prob_shift(self, baseline: Dict[str, float], skill: Dict[str, float]) -> float:
        """
        Calculates the log-probability shift between baseline and skill distributions.
        Uses KL-divergence approximation or simple log-prob difference for the selected action.
        Here we use the difference in log-prob of the selected action (max prob) for simplicity.
        """
        import math
        selected = max(baseline, key=baseline.get)
        
        p_baseline = baseline.get(selected, 1e-9)
        p_skill = skill.get(selected, 1e-9)
        
        # Avoid log(0)
        p_baseline = max(p_baseline, 1e-9)
        p_skill = max(p_skill, 1e-9)
        
        shift = math.log(p_skill) - math.log(p_baseline)
        return shift

def main():
    """
    Entry point for standalone testing of the router.
    Simulates a few routing decisions to demonstrate logging.
    """
    config = OPIDRouterConfig(routing_threshold=0.5, seed=42)
    router = OPIDRouter(config)

    # Mock data for demonstration
    baseline_probs = {"action_a": 0.8, "action_b": 0.2}
    skill_probs = {"action_a": 0.2, "action_b": 0.8}

    print("Running OPID Router Demo...")
    for i in range(10):
        action, probs, info = router.route(None, baseline_probs, skill_probs)
        print(f"Step {i}: Action={action}, Injected={info['injected']}, LogShift={info['log_shift']:.4f}")

    print(f"Logs written to {config.log_file}")

if __name__ == "__main__":
    main()