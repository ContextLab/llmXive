"""
Student Policy for TOP-D Training.

A capacity-constrained policy that learns to approximate the teacher's behavior
while respecting a cognitive horizon limit.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from utils.logger import get_logger
from env.reasoning_mdp import ReasoningMDP

logger = get_logger("student_policy")

class StudentPolicy:
    def __init__(self, env: ReasoningMDP, horizon_limit: int = 5):
        self.env = env
        self.horizon_limit = horizon_limit
        self.current_depth = 0
        self.step_count = 0
        
        # Simple Q-table for this small environment
        # Q[state, action]
        self.q_table = np.zeros((env.size + 1, env.action_space))
        self.learning_rate = 0.1
        self.discount_factor = 0.9

    def select_action(self, state: int) -> int:
        """
        Select action based on current policy and horizon constraint.
        """
        # Horizon enforcement: if we've taken too many steps without progress, force reset or penalty
        # In this simple env, we just limit the depth we attempt to plan for
        
        # Epsilon-greedy for exploration (simplified)
        if np.random.rand() < 0.1:
            return np.random.randint(self.env.action_space)
        
        return np.argmax(self.q_table[state])

    def get_action_distribution(self, state: int) -> np.ndarray:
        """
        Return a probability distribution over actions (for loss calculation).
        Softmax over Q-values.
        """
        q_vals = self.q_table[state]
        # Softmax
        exp_q = np.exp(q_vals - np.max(q_vals))
        return exp_q / np.sum(exp_q)

    def update(self, state: int, action: int, reward: float, next_state: int):
        """Update Q-table."""
        best_next = np.max(self.q_table[next_state])
        td_target = reward + self.discount_factor * best_next
        td_error = td_target - self.q_table[state, action]
        self.q_table[state, action] += self.learning_rate * td_error

    def reset(self):
        self.current_depth = 0
        self.step_count = 0
