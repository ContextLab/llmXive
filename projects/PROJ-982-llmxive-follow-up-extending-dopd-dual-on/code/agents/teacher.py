"""
Teacher Oracle Agent with full state access.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any
import sys
import os

# Ensure the project root is in the Python path so that imports work correctly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything

class TeacherOracle:
    """
    Oracle policy agent with access to full state (O, H).
    Uses Value Iteration to compute optimal Q-table.
    """
    
    def __init__(self, env: PrivilegeMDP, gamma: float = 0.99, tol: float = 1e-6):
        """
        Initialise the teacher oracle.

        Args:
            env: The PrivilegeMDP environment.
            gamma: Discount factor for value iteration.
            tol: Convergence tolerance for value iteration (maximum change in V across
                 all states below this value terminates the iteration).
        """
        self.env = env
        self.gamma = gamma
        self.tol = tol
        self.q_table: np.ndarray | None = None
        self.v_table: np.ndarray | None = None
        self._compute_optimal_policy()

    # ----------------------------------------------------------------------
    # Value‑iteration implementation
    # ----------------------------------------------------------------------
    def _compute_optimal_policy(self):
        """Compute the optimal Q‑table using standard value iteration."""
        grid_size = self.env.grid_size
        num_states = grid_size * grid_size * 2               # (x, y, h)
        num_actions = self.env.action_space

        # Initialise tables
        self.q_table = np.zeros((num_states, num_actions))
        self.v_table = np.zeros(num_states)

        # Value‑iteration loop
        for iteration in range(10_000):  # hard upper bound to avoid infinite loops
            delta = 0.0

            for s in range(num_states):
                # Decode the flat state index back to (x, y, h)
                h = s // (grid_size * grid_size)
                xy = s % (grid_size * grid_size)
                y = xy // grid_size
                x = xy % grid_size

                # Determine the goal location based on the privileged variable h
                if h == 1:
                    goal_x, goal_y = grid_size - 1, grid_size - 1
                else:
                    goal_x, goal_y = 0, 0

                best_v = -np.inf

                # Evaluate all actions to find the best expected return
                for a in range(num_actions):
                    # Simulate deterministic transition
                    next_x, next_y = x, y
                    if a == 0:   # Up
                        next_y = min(y + 1, grid_size - 1)
                    elif a == 1: # Down
                        next_y = max(y - 1, 0)
                    elif a == 2: # Left
                        next_x = max(x - 1, 0)
                    elif a == 3: # Right
                        next_x = min(x + 1, grid_size - 1)

                    # Reward and terminal check
                    if next_x == goal_x and next_y == goal_y:
                        reward = self.env.goal_reward
                        done = True
                    else:
                        reward = self.env.step_penalty
                        done = False

                    # Compute the index of the successor state (h does not change)
                    next_xy = next_y * grid_size + next_x
                    next_s = h * grid_size * grid_size + next_xy

                    # Bellman backup
                    if done:
                        q_val = reward
                    else:
                        q_val = reward + self.gamma * self.v_table[next_s]

                    if q_val > best_v:
                        best_v = q_val

                # Track the maximum change for convergence testing
                delta = max(delta, abs(best_v - self.v_table[s]))
                self.v_table[s] = best_v

            if delta < self.tol:
                # Converged – stop iterating
                break

        # Populate the full Q‑table now that V‑values are known
        for s in range(num_states):
            h = s // (grid_size * grid_size)
            xy = s % (grid_size * grid_size)
            y = xy // grid_size
            x = xy % grid_size

            if h == 1:
                goal_x, goal_y = grid_size - 1, grid_size - 1
            else:
                goal_x, goal_y = 0, 0

            for a in range(num_actions):
                # Simulate transition (same as above)
                next_x, next_y = x, y
                if a == 0:
                    next_y = min(y + 1, grid_size - 1)
                elif a == 1:
                    next_y = max(y - 1, 0)
                elif a == 2:
                    next_x = max(x - 1, 0)
                elif a == 3:
                    next_x = min(x + 1, grid_size - 1)

                if next_x == goal_x and next_y == goal_y:
                    reward = self.env.goal_reward
                    done = True
                else:
                    reward = self.env.step_penalty
                    done = False

                next_xy = next_y * grid_size + next_x
                next_s = h * grid_size * grid_size + next_xy

                if done:
                    self.q_table[s, a] = reward
                else:
                    self.q_table[s, a] = reward + self.gamma * self.v_table[next_s]

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def select_action(self, state: np.ndarray) -> int:
        """
        Return the optimal action for a given full state (x, y, h).

        Args:
            state: A NumPy array or sequence ``[x, y, h]``.

        Returns:
            Integer index of the optimal action according to the cached Q‑table.
        """
        grid_size = self.env.grid_size
        x, y, h = state
        s = h * grid_size * grid_size + y * grid_size + x
        return int(np.argmax(self.q_table[s]))

    def get_q_value(self, state: np.ndarray, action: int) -> float:
        """
        Query the stored Q‑value for a particular (state, action) pair.

        Args:
            state: Full state ``[x, y, h]``.
            action: Action index.

        Returns:
            The Q‑value as a float.
        """
        grid_size = self.env.grid_size
        x, y, h = state
        s = h * grid_size * grid_size + y * grid_size + x
        return float(self.q_table[s, action])

    def get_v_value(self, state: np.ndarray) -> float:
        """
        Query the stored state‑value V(s) for a full state.

        Args:
            state: Full state ``[x, y, h]``.

        Returns:
            The V‑value as a float.
        """
        grid_size = self.env.grid_size
        x, y, h = state
        s = h * grid_size * grid_size + y * grid_size + x
        return float(self.v_table[s])

def create_teacher_agent(env: PrivilegeMDP) -> TeacherOracle:
    """
    Factory helper used throughout the code‑base and tests.

    Args:
        env: The PrivilegeMDP environment.

    Returns:
        An instantiated ``TeacherOracle`` with its optimal Q‑table already cached.
    """
    return TeacherOracle(env)
