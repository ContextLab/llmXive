"""
OPID routing logic with a configurable threshold.
"""

import random
from dataclasses import dataclass

@dataclass
class OPIDRouterConfig:
    routing_threshold: float = 1.0  # 0.0 = always inject, 1.0 = never inject

class OPIDRouter:
    def __init__(self, routing_threshold: float = 1.0):
        if not 0.0 <= routing_threshold <= 1.0:
            raise ValueError("routing_threshold must be between 0.0 and 1.0")
        self.routing_threshold = routing_threshold

    def should_inject(self) -> bool:
        """Return True if a skill injection should occur."""
        return random.random() < (1.0 - self.routing_threshold)

    def inject_skill_signal(self, action_probs):
        """Placeholder for signal injection – not used in this stub."""
        return action_probs