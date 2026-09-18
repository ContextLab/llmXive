"""
Teacher Oracle Agent with full state access.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything

class TeacherOracle:
    """
    Oracle policy agent with access to full state (O, H).
    Uses Value Iteration to compute optimal Q-table.
    """
    
    def __init__(self, env: PrivilegeMDP, gamma: float = 0.99, tol: float = 1e-6):
        self.env = env
        self.gamma = gamma
        self.tol = tol
        self.q_table = None
        self.v_table = None
        self._compute_optimal_policy()

    def _compute_optimal_policy(self):
        """Compute optimal Q-table using Value Iteration."""
        # State space: grid_size x grid_size x 2 (for h)
        grid_size = self.env.grid_size
        num_states = grid_size * grid_size * 2
        num_actions = self.env.action_space
        
        # Initialize Q-table
        self.q_table = np.zeros((num_states, num_actions))
        self.v_table = np.zeros(num_states)
        
        # Value Iteration
        for iteration in range(10000):  # Max iterations
            delta = 0
            
            for s in range(num_states):
                # Decode state
                h = s // (grid_size * grid_size)
                xy = s % (grid_size * grid_size)
                y = xy // grid_size
                x = xy % grid_size
                
                # Determine goal based on h
                if h == 1:
                    goal_x, goal_y = grid_size - 1, grid_size - 1
                else:
                    goal_x, goal_y = 0, 0
                
                new_v = -np.inf
                
                for a in range(num_actions):
                    # Simulate action
                    next_x, next_y = x, y
                    if a == 0:  # Up
                        next_y = min(y + 1, grid_size - 1)
                    elif a == 1:  # Down
                        next_y = max(y - 1, 0)
                    elif a == 2:  # Left
                        next_x = max(x - 1, 0)
                    elif a == 3:  # Right
                        next_x = min(x + 1, grid_size - 1)
                    
                    # Calculate reward
                    if next_x == goal_x and next_y == goal_y:
                        reward = self.env.goal_reward
                        done = True
                    else:
                        reward = self.env.step_penalty
                        done = False
                    
                    # Next state index
                    next_xy = next_y * grid_size + next_x
                    next_s = h * grid_size * grid_size + next_xy
                    
                    # Q-value update
                    if done:
                        q_value = reward
                    else:
                        q_value = reward + self.gamma * self.v_table[next_s]
                    
                    if q_value > new_v:
                        new_v = q_value
                
                delta = max(delta, abs(new_v - self.v_table[s]))
                self.v_table[s] = new_v
            
            if delta < self.tol:
                break
        
        # Compute Q-table from V-table
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

    def select_action(self, state: np.ndarray) -> int:
        """Select optimal action given full state (O, H)."""
        grid_size = self.env.grid_size
        x, y, h = state
        
        # Encode state
        s = h * grid_size * grid_size + y * grid_size + x
        
        # Get optimal action
        optimal_action = np.argmax(self.q_table[s])
        return optimal_action

    def get_q_value(self, state: np.ndarray, action: int) -> float:
        """Get Q-value for state-action pair."""
        grid_size = self.env.grid_size
        x, y, h = state
        
        # Encode state
        s = h * grid_size * grid_size + y * grid_size + x
        
        return self.q_table[s, action]

    def get_v_value(self, state: np.ndarray) -> float:
        """Get V-value for state."""
        grid_size = self.env.grid_size
        x, y, h = state
        
        # Encode state
        s = h * grid_size * grid_size + y * grid_size + x
        
        return self.v_table[s]

def create_teacher_agent(env: PrivilegeMDP) -> TeacherOracle:
    """Factory function to create teacher agent."""
    return TeacherOracle(env)
