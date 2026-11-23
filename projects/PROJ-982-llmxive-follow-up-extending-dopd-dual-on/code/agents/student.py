"""
Tabular Q‑Learning Student Agent with partial state access (observable only).

This implementation satisfies the unit test expectations for T020:
* ε‑greedy action selection (`select_action`).
* TD‑error based Q‑table update via `update(observation, action, td_error)`.
* Backwards‑compatible `update_q_table` used by existing training loops.
* No access to the hidden privileged variable `h` – only the (x, y) observation is used.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
import sys
import os

# Ensure the project root (the ``code`` directory) is on ``sys.path`` so that
# relative imports work even when this file is executed as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything


class TabularQStudent:
    """
    Tabular Q‑learning agent that only observes the observable part of the state
    (x, y). The hidden privileged variable ``h`` is never accessed.
    """

    def __init__(
        self,
        env: PrivilegeMDP,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        min_epsilon: float = 0.01,
        seed: Optional[int] = None,
    ):
        """
        Initialise the student.

        Args:
            env: The PrivilegeMDP environment (used for grid size and action space).
            learning_rate: Base learning rate α for Q‑updates.
            discount_factor: Discount factor γ.
            epsilon: Initial ε for ε‑greedy exploration.
            epsilon_decay: Multiplicative decay applied after each update.
            min_epsilon: Lower bound for ε.
            seed: Optional seed for reproducibility.
        """
        self.env = env
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

        # Q‑table indexed by observable state (flattened x,y) and action.
        grid_size = env.grid_size
        self.q_table = np.zeros((grid_size * grid_size, env.action_space))

        # Random generator for exploration.
        if seed is not None:
            seed_everything(seed)
            self.rng = np.random.RandomState(seed)
        else:
            self.rng = np.random.RandomState()

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _obs_to_index(self, obs: np.ndarray) -> int:
        """
        Convert a (x, y) observation into a flat index into the Q‑table.

        Args:
            obs: ``np.ndarray`` of shape (2,) containing integer x and y.

        Returns:
            Integer index in ``[0, grid_size*grid_size)``.
        """
        x, y = obs
        grid_size = self.env.grid_size
        return int(y * grid_size + x)

    # ------------------------------------------------------------------
    # Action selection
    # ------------------------------------------------------------------
    def select_action(self, obs: np.ndarray, training: bool = True) -> int:
        """
        Choose an action using an ε‑greedy policy.

        Args:
            obs: Observable state (x, y) as a NumPy array.
            training: If ``True`` the agent may explore; otherwise it acts
                      greedily.

        Returns:
            Integer action index in ``[0, env.action_space)``.
        """
        idx = self._obs_to_index(obs)

        if training and self.rng.random() < self.epsilon:
            # Exploration: random action.
            return int(self.rng.randint(0, self.env.action_space))

        # Exploitation: greedy action with highest Q‑value.
        return int(np.argmax(self.q_table[idx]))

    # ------------------------------------------------------------------
    # Q‑table updates
    # ------------------------------------------------------------------
    def update(self, obs: np.ndarray, action: int, td_error: float) -> None:
        """
        Perform a TD‑error update on the Q‑table.

        This method matches the signature required by the unit test
        ``code/tests/unit/test_student.py``.

        Args:
            obs: Current observable state (x, y).
            action: Action taken in that state.
            td_error: The TD error δ = r + γ·max_a' Q(s',a') − Q(s,a).
        """
        idx = self._obs_to_index(obs)
        # Simple TD update: Q ← Q + α·δ
        self.q_table[idx, action] += self.learning_rate * td_error

        # Decay ε after each update (if not already at the minimum).
        if self.epsilon > self.min_epsilon:
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def update_q_table(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        next_obs: np.ndarray,
        learning_rate: Optional[float] = None,
    ) -> None:
        """
        Backwards‑compatible update method used by the existing training
        loops (e.g., DOPD). It computes the TD error internally and then
        delegates to :meth:`update`.

        Args:
            obs: Current observation (x, y).
            action: Action taken.
            reward: Immediate reward received.
            next_obs: Observation after the transition.
            learning_rate: Optional override for the learning rate α.
        """
        lr = self.learning_rate if learning_rate is None else learning_rate
        idx = self._obs_to_index(obs)
        next_idx = self._obs_to_index(next_obs)

        # Compute the TD error.
        td_error = reward + self.discount_factor * np.max(self.q_table[next_idx]) - self.q_table[idx, action]

        # Apply the update using the possibly overridden learning rate.
        # Temporarily adjust the instance's learning_rate if an override is given.
        original_lr = self.learning_rate
        self.learning_rate = lr
        self.update(obs, action, td_error)
        self.learning_rate = original_lr  # restore original value

    # ------------------------------------------------------------------
    # Action‑probability utilities (useful for logging / analysis)
    # ------------------------------------------------------------------
    def get_action_probs(self, obs: np.ndarray) -> np.ndarray:
        """
        Return a softmax distribution over actions for the given observation.

        Args:
            obs: Observable state (x, y).

        Returns:
            ``np.ndarray`` of shape ``(env.action_space,)`` summing to 1.
        """
        idx = self._obs_to_index(obs)
        q_vals = self.q_table[idx]

        # Numerical‑stable softmax.
        shifted = q_vals - np.max(q_vals)
        exp_q = np.exp(shifted)
        probs = exp_q / np.sum(exp_q)
        return probs


def create_student_agent(env: PrivilegeMDP, seed: Optional[int] = None) -> TabularQStudent:
    """
    Factory function used throughout the code‑base and tests.

    Args:
        env: The PrivilegeMDP environment.
        seed: Optional seed for reproducibility.

    Returns:
        An instantiated ``TabularQStudent``.
    """
    return TabularQStudent(env, seed=seed)