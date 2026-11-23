"""
Baseline Value Estimator using Monte Carlo simulation.
"""
import numpy as np
from typing import Tuple, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything
from agents.random_policy import RandomPolicyAgent

class BaselineEstimator:
    """
    Estimates state-value function V_baseline(s) using Monte Carlo simulation
    with a random policy.
    """
    
    def __init__(self, env: PrivilegeMDP, batch_size: int = 10, 
                 max_iterations: int = 10000, convergence_threshold: float = 0.01,
                 convergence_window: int = 100, seed: int = None):
        self.env = env
        self.batch_size = batch_size
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.convergence_window = convergence_window
        self.seed = seed
        
        # Initialize V-table
        grid_size = env.grid_size
        num_states = grid_size * grid_size * 2  # Include h dimension
        self.v_baseline = np.zeros(num_states)
        self.counts = np.zeros(num_states)
        
        self.is_converged = False
        
        if seed is not None:
            seed_everything(seed)

    def _get_state_index(self, x: int, y: int, h: int) -> int:
        """Convert (x, y, h) to flat index."""
        grid_size = self.env.grid_size
        return h * grid_size * grid_size + y * grid_size + x

    def estimate_v_baseline(self) -> bool:
        """
        Run Monte Carlo simulation to estimate V_baseline.
        
        Returns:
            True if converged, False otherwise.
        """
        random_agent = RandomPolicyAgent(self.env)
        
        recent_stds = []
        
        for iteration in range(self.max_iterations):
            # Run batch of episodes
            returns = []
            
            for _ in range(self.batch_size):
                episode_returns = self._run_episode(random_agent)
                returns.extend(episode_returns)
            
            # Update V-table
            for state_idx, return_val in returns:
                self.v_baseline[state_idx] += return_val
                self.counts[state_idx] += 1
            
            # Normalize
            for s in range(len(self.v_baseline)):
                if self.counts[s] > 0:
                    self.v_baseline[s] /= self.counts[s]
            
            # Check convergence
            if len(returns) > 0:
                current_std = np.std([r[1] for r in returns])
                recent_stds.append(current_std)
                
                if len(recent_stds) > self.convergence_window:
                    recent_stds.pop(0)
                
                if len(recent_stds) == self.convergence_window:
                    avg_std = np.mean(recent_stds)
                    if avg_std < self.convergence_threshold:
                        self.is_converged = True
                        return True
        
        if not self.is_converged:
            print(f"Warning: V_baseline did not converge after {self.max_iterations} iterations")
        
        return self.is_converged

    def _run_episode(self, agent) -> List[Tuple[int, float]]:
        """Run a single episode and collect (state_idx, return) pairs."""
        state = self.env.reset(seed=self.seed)
        done = False
        episode_states = []
        episode_rewards = []
        
        while not done:
            action = agent.select_action(state)
            next_state, reward, done, info = self.env.step(action)
            
            # Record state (with hidden info for baseline)
            full_state = self.env.get_state()
            x, y, h = full_state
            state_idx = self._get_state_index(x, y, h)
            
            episode_states.append(state_idx)
            episode_rewards.append(reward)
            
            state = next_state
        
        # Calculate returns
        returns = []
        G = 0
        gamma = 0.99
        
        for r in reversed(episode_rewards):
            G = r + gamma * G
            returns.append(G)
        
        returns.reverse()
        
        return list(zip(episode_states, returns))

    def get_v_baseline(self, state: np.ndarray) -> float:
        """Get V_baseline value for a state."""
        x, y, h = state
        state_idx = self._get_state_index(x, y, h)
        return self.v_baseline[state_idx]

def create_baseline_estimator(env: PrivilegeMDP, seed: int = None) -> BaselineEstimator:
    """Factory function to create baseline estimator."""
    estimator = BaselineEstimator(env, seed=seed)
    estimator.estimate_v_baseline()
    return estimator
