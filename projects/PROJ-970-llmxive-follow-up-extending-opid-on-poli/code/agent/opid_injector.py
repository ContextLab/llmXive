import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from config import get_seed, set_seed

logger = logging.getLogger(__name__)

@dataclass
class OPIDInjectorConfig:
    """Configuration for the Hindsight Skill Distillation Injector."""
    injection_strength: float = 0.5
    min_log_prob_shift: float = -1.0
    max_log_prob_shift: float = 1.0
    seed: Optional[int] = None

class OPIDInjector:
    """
    Handles the injection of hindsight skill distillation signals into the agent's
    policy based on the routing outcome determined by the OPIDRouter.

    This module implements the core logic for modifying the action distribution
    when a 'critical' path is detected and skill injection is triggered.
    """

    def __init__(self, config: OPIDInjectorConfig):
        self.config = config
        if config.seed is not None:
            set_seed(config.seed)
        self._injection_count = 0
        self._total_injection_attempts = 0

    def inject_skill_signal(
        self,
        current_log_probs: np.ndarray,
        action: int,
        routing_decision: bool,
        state_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Injects hindsight skill distillation signals into the log-probabilities
        if the routing decision indicates injection should occur.

        Args:
            current_log_probs: The current log-probabilities of the policy (numpy array).
            action: The action selected by the baseline policy.
            routing_decision: Boolean result from the OPIDRouter Bernoulli trial.
                              True = Inject, False = Suppress.
            state_context: Optional dictionary containing state features (e.g., 'tier', 'step').

        Returns:
            A tuple containing:
                - modified_log_probs: The updated log-probabilities after potential injection.
                - metadata: A dictionary with injection stats and shift details.
        """
        self._total_injection_attempts += 1
        metadata = {
            "injected": False,
            "original_action_log_prob": float(current_log_probs[action]),
            "shift_magnitude": 0.0,
            "reason": "Routing decision was False (suppression)"
        }

        if not routing_decision:
            return current_log_probs, metadata

        # Logic for Hindsight Skill Distillation Injection
        # 1. Identify the 'hindsight optimal' action.
        #    In this context, we assume the 'action' passed is the one taken,
        #    but for distillation, we often reinforce the action that *should*
        #    have been taken or reinforce the taken action if it was critical.
        #    For this implementation, we reinforce the 'action' provided as
        #    the 'hindsight' signal for the critical path.
        
        target_action = action
        
        # Calculate the shift magnitude based on config and context
        base_shift = self.config.injection_strength
        
        # Optional: Modulate shift based on state context (e.g., higher tier = higher confidence)
        if state_context and 'tier' in state_context:
            tier = state_context['tier']
            if tier == 3:
                base_shift *= 1.2 # Slightly higher confidence in high entropy tiers
            elif tier == 1:
                base_shift *= 0.8 # Slightly lower in deterministic tiers

        # Apply the shift to the target action
        # We use a soft-clamping mechanism to ensure numerical stability
        shift = np.clip(base_shift, self.config.min_log_prob_shift, self.config.max_log_prob_shift)
        
        modified_log_probs = current_log_probs.copy()
        
        # Add the positive shift to the target action
        modified_log_probs[target_action] += shift
        
        # Renormalize (softmax in log space: subtract log-sum-exp) to keep valid distribution
        # log_p_new = log_p + shift (for target), log_p (others)
        # To maintain sum(exp(log_p)) = 1, we subtract log(sum(exp(log_p_new)))
        max_log_p = np.max(modified_log_probs)
        log_sum_exp = max_log_p + np.log(np.sum(np.exp(modified_log_probs - max_log_p)))
        modified_log_probs -= log_sum_exp

        # Calculate the actual shift experienced
        actual_shift = float(modified_log_probs[target_action] - current_log_probs[target_action])
        
        metadata.update({
            "injected": True,
            "target_action": int(target_action),
            "shift_magnitude": float(shift),
            "actual_shift": actual_shift,
            "reason": "Routing decision was True (injection triggered)",
            "state_context": state_context
        })

        self._injection_count += 1
        logger.debug(
            f"Skill signal injected. Action: {target_action}, Shift: {actual_shift:.4f}, "
            f"Tier: {state_context.get('tier', 'N/A') if state_context else 'N/A'}"
        )

        return modified_log_probs, metadata

    def get_stats(self) -> Dict[str, Any]:
        """Returns current injection statistics."""
        return {
            "total_attempts": self._total_injection_attempts,
            "successful_injections": self._injection_count,
            "injection_rate": (
                self._injection_count / self._total_injection_attempts
                if self._total_injection_attempts > 0 else 0.0
            )
        }

def main():
    """
    Standalone runner to demonstrate the OPIDInjector functionality.
    Simulates a routing decision and injects a signal.
    """
    from config import ensure_directories
    ensure_directories()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize config
    config = OPIDInjectorConfig(
        injection_strength=0.8,
        seed=42
    )
    
    injector = OPIDInjector(config)
    
    # Simulate a policy distribution (log probabilities for 5 actions)
    # Softmax of [0.1, 0.2, 0.3, 0.2, 0.2] roughly
    raw_logits = np.array([0.1, 0.2, 0.3, 0.2, 0.2])
    # Convert to log-probs (assuming these are already logits, but let's normalize to log-probs)
    # For demonstration, we treat raw_logits as log-probs directly or normalize them
    max_l = np.max(raw_logits)
    log_probs = raw_logits - (max_l + np.log(np.sum(np.exp(raw_logits - max_l))))
    
    print(f"Original Log-Probabilities: {log_probs}")
    print(f"Sum of Exp(Log-Prob): {np.sum(np.exp(log_probs))}")
    
    # Simulate a routing decision (True = Inject)
    # In real flow, this comes from OPIDRouter
    routing_decision = True 
    selected_action = 2 # Index of the max prob action
    context = {"tier": 2, "step": 10}
    
    new_log_probs, metadata = injector.inject_skill_signal(
        current_log_probs=log_probs,
        action=selected_action,
        routing_decision=routing_decision,
        state_context=context
    )
    
    print(f"\nRouting Decision: {routing_decision}")
    print(f"Injected Log-Probabilities: {new_log_probs}")
    print(f"Sum of Exp(New Log-Prob): {np.sum(np.exp(new_log_probs))}")
    print(f"Metadata: {metadata}")
    
    # Verify normalization
    assert np.isclose(np.sum(np.exp(new_log_probs)), 1.0), "Probability distribution not normalized!"
    print("\nVerification passed: Distribution is valid.")

if __name__ == "__main__":
    main()