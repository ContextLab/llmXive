"""
Random Policy Agent for baseline estimation.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP

class RandomPolicyAgent:
    """
    Agent that selects actions uniformly at random.
    """
    
    def __init__(self, env: PrivilegeMDP, seed: int = None):
        self.env = env
        self.rng = np.random.RandomState(seed)

    def select_action(self, state: np.ndarray) -> int:
        """Select a random action."""
        return self.rng.randint(0, self.env.action_space)

def create_random_policy(env: PrivilegeMDP, seed: int = None) -> RandomPolicyAgent:
    """Factory function to create random policy agent."""
    return RandomPolicyAgent(env, seed=seed)