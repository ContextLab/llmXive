"""
Tabular Q-Learning Student Agent with partial state access (O only).
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything

class TabularQStudent:
    """
    Tabular Q-learning agent that only observes O (not H).
    """
    
    def __init__(self, env: PrivilegeMDP, learning_rate: float = 0.1, 
                 discount_factor: float = 0.99, epsilon: float = 0.1,
                 epsilon_decay: float = 0.995, min_epsilon: float = 0.01,
                 seed: int = None):
        self.env = env
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        
        # Q-table: observation space (grid_size x grid_size) x action_space
        grid_size = env.grid_size
        self.q_table = np.zeros((grid_size * grid_size, env.action_space))
        
        if seed is not None:
            seed_everything(seed)
            self.rng = np.random.RandomState(seed)
        else:
            self.rng = np.random.RandomState()

    def get_obs_index(self, obs: np.ndarray) -> int:
        """Convert observation to flat index."""
        x, y = obs
        grid_size = self.env.grid_size
        return y * grid_size + x

    def select_action(self, obs: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            obs: Observation vector (x, y).
            training: If True, use exploration; else, exploit.
        
        Returns:
            Selected action index.
        """
        obs_idx = self.get_obs_index(obs)
        
        if training and self.rng.random() < self.epsilon:
            # Explore: random action
            return self.rng.randint(0, self.env.action_space)
        else:
            # Exploit: greedy action
            return np.argmax(self.q_table[obs_idx])

    def update_q_table(self, obs: np.ndarray, action: int, reward: float,
                       next_obs: np.ndarray, learning_rate: float = None):
        """
        Update Q-table using Q-learning update rule.
        
        Args:
            obs: Current observation.
            action: Action taken.
            reward: Reward received.
            next_obs: Next observation.
            learning_rate: Override learning rate if provided.
        """
        if learning_rate is None:
            lr = self.learning_rate
        else:
            lr = learning_rate
        
        obs_idx = self.get_obs_index(obs)
        next_obs_idx = self.get_obs_index(next_obs)
        
        # Q-learning update
        current_q = self.q_table[obs_idx, action]
        next_max_q = np.max(self.q_table[next_obs_idx])
        
        new_q = current_q + lr * (reward + self.discount_factor * next_max_q - current_q)
        self.q_table[obs_idx, action] = new_q
        
        # Decay epsilon
        if self.epsilon > self.min_epsilon:
            self.epsilon *= self.epsilon_decay

    def get_action_probs(self, obs: np.ndarray) -> np.ndarray:
        """
        Get action probabilities based on current Q-values.
        Uses softmax for exploration analysis.
        """
        obs_idx = self.get_obs_index(obs)
        q_values = self.q_table[obs_idx]
        
        # Softmax
        exp_q = np.exp(q_values - np.max(q_values))  # Numerical stability
        probs = exp_q / np.sum(exp_q)
        
        return probs

def create_student_agent(env: PrivilegeMDP, seed: int = None) -> TabularQStudent:
    """Factory function to create student agent."""
    return TabularQStudent(env, seed=seed)
