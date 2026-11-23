"""
Baseline policy implementation (softmax over random logits).
"""

import math
import random
from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class BaselinePolicyConfig:
    policy_type: str = "softmax"
    temperature: float = 1.0
    seed: int = 42

class BaselinePolicy:
    def __init__(self, config: BaselinePolicyConfig):
        if config.temperature <= 0:
            raise ValueError("temperature must be positive")
        self.config = config
        random.seed(config.seed)

    @property
    def policy_type(self):
        return self.config.policy_type

    @property
    def temperature(self):
        return self.config.temperature

    @property
    def seed(self):
        return self.config.seed

    def select_action(self, node, graph):
        """
        Return (action_node_id, log_prob) for the given state.
        """
        # Determine possible outgoing edges
        outgoing = [e for e in graph.edges if e.source == node.id]
        if not outgoing:
            return None, 0.0

        # Compute logits (random for this stub)
        logits = [random.random() for _ in outgoing]
        # Apply temperature
        scaled = [l / self.temperature for l in logits]
        # Softmax
        max_logit = max(scaled)
        exp_vals = [math.exp(l - max_logit) for l in scaled]
        total = sum(exp_vals)
        probs = [v / total for v in exp_vals]

        # Sample an action
        choice = random.choices(outgoing, weights=probs, k=1)[0]
        log_prob = math.log(probs[outgoing.index(choice)])
        return choice.target, log_prob

def create_baseline_policy(config: BaselinePolicyConfig = None) -> BaselinePolicy:
    """Factory function for a baseline policy."""
    if config is None:
        config = BaselinePolicyConfig()
    return BaselinePolicy(config)