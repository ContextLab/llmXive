"""
Teacher Agent: Oracle Policy for the Privilege MDP.

The Teacher has full access to the state (O, H) and computes the optimal action
using a pre-computed value function or direct lookup of the optimal policy.
In this discrete MDP, the Teacher acts as the "Oracle" that the Student attempts
to distill.
"""
from typing import Tuple, Optional, Dict, Any
import numpy as np

from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything


class TeacherOracle:
    """
    An oracle agent that knows the hidden state H and the observable state O.
    It computes the optimal action based on the full state (O, H).
    """

    def __init__(self, env: PrivilegeMDP, seed: Optional[int] = None):
        """
        Initialize the Teacher Oracle.

        Args:
            env: The PrivilegeMDP environment instance.
            seed: Optional seed for reproducibility if randomization is needed
                  (though the Oracle is deterministic given the state).
        """
        self.env = env
        self.seed = seed

        if seed is not None:
            seed_everything(seed)

        # Pre-compute the optimal value function and policy.
        # Since the MDP is discrete and small (grid-world), we use Value Iteration.
        self._compute_optimal_policy()

    def _compute_optimal_policy(self) -> None:
        """
        Computes the optimal Q-function and Policy using Value Iteration.
        The state space is defined by (grid_pos, hidden_signal).
        """
        # Extract dimensions
        n_grid_cells = self.env.grid_size ** 2
        n_hidden_states = self.env.hidden_signal_levels
        n_actions = self.env.action_space.n

        # Total state space size: (grid_pos, hidden_signal)
        total_states = n_grid_cells * n_hidden_states

        # Initialize Value function V(s) = 0
        # State index mapping: s = grid_idx * n_hidden_states + h_idx
        V = np.zeros(total_states)

        # Discount factor
        gamma = self.env.gamma

        # Iteration parameters
        max_iterations = 1000
        threshold = 1e-6

        for iteration in range(max_iterations):
            delta = 0.0
            new_V = np.zeros(total_states)

            for grid_idx in range(n_grid_cells):
                for h_idx in range(n_hidden_states):
                    s_idx = grid_idx * n_hidden_states + h_idx
                    v_old = V[s_idx]
                    q_values = []

                    # Get current grid position and hidden state
                    # We need to reverse the index to get (x, y)
                    x = grid_idx // self.env.grid_size
                    y = grid_idx % self.env.grid_size

                    # Evaluate all actions
                    for a in range(n_actions):
                        # Simulate transition to get reward and next state
                        # We use the env's logic but without stepping the actual env
                        # to avoid side effects.
                        # We need to calculate the expected return for action a in state s.
                        
                        # Determine next state based on deterministic or stochastic transitions
                        # For this discrete MDP, let's assume standard grid dynamics:
                        # - Action moves agent, H might change or stay, but H is the "privileged" signal.
                        # - The env's step function returns (obs, reward, terminated, truncated, info).
                        # - We need to iterate over possible next states if stochastic.
                        
                        # Since we are implementing the Oracle, we assume we know the transition dynamics P(s'|s,a).
                        # We will approximate this by running the env's step logic for all possible outcomes.
                        # However, to keep it simple and deterministic for the "Oracle",
                        # we will use the env's deterministic transition logic if available,
                        # or sample the expected value if stochastic.
                        
                        # Let's assume the env.step is deterministic for the purpose of the Oracle's planning
                        # or we iterate over the support of the transition.
                        
                        # We need to construct the 'full state' for the env's internal logic.
                        # The envPrivilegeMDP likely stores state as (grid_pos, hidden_signal).
                        # We need to peek into the env to understand the transition.
                        # Since we can't easily call env.step without side effects on the internal state,
                        # we replicate the transition logic or use a temporary step.
                        
                        # Strategy: Temporarily set env state, step, record, restore.
                        # This is safe because we do it in a loop and don't yield.
                        
                        # Save current env state
                        saved_state = (self.env.grid_pos, self.env.hidden_signal)
                        
                        # Set to current s
                        self.env.grid_pos = (x, y)
                        self.env.hidden_signal = h_idx
                        
                        # Step
                        obs, reward, terminated, truncated, info = self.env.step(a)
                        
                        # Restore
                        self.env.grid_pos, self.env.hidden_signal = saved_state
                        
                        # Calculate next state index
                        # obs is the observation (O), which might not include H.
                        # But the internal state of the env is (grid_pos, hidden_signal).
                        # We need the NEXT full state (grid_pos', hidden_signal').
                        # The step function returns 'info' which might contain the next full state,
                        # or we can infer it from the env's internal state after the step.
                        # Since we restored the state, we can't see the new one easily unless we track it.
                        
                        # Better approach: The env.step modifies self.grid_pos and self.hidden_signal.
                        # We just restored it. We need to know where it WOULD go.
                        # Let's look at the env implementation details we have access to.
                        # We don't have the full code of privilege_mdp.py, but we know it's a grid world.
                        # Let's assume standard dynamics:
                        # - Action moves grid_pos.
                        # - hidden_signal might be static or change based on some rule.
                        # - The env.step returns 'info' with 'next_state' or similar?
                        # - If not, we must rely on the env's internal state logic.
                        
                        # Alternative: Use the env's internal state after step, but we must NOT restore it yet.
                        # Actually, we can just read the env's state after step before restoring.
                        # But we must ensure we don't break the env if it's used concurrently (unlikely here).
                        
                        # Let's re-do the step and read the new state directly.
                        self.env.grid_pos = (x, y)
                        self.env.hidden_signal = h_idx
                        obs, reward, terminated, truncated, info = self.env.step(a)
                        next_grid_pos = self.env.grid_pos
                        next_hidden_signal = self.env.hidden_signal
                        
                        # Restore
                        self.env.grid_pos, self.env.hidden_signal = saved_state
                        
                        # Map next state to index
                        next_grid_idx = next_grid_pos[0] * self.env.grid_size + next_grid_pos[1]
                        next_s_idx = next_grid_idx * n_hidden_states + next_hidden_signal
                        
                        # If terminal, value is 0 (or reward of terminal, usually handled in reward)
                        if terminated or truncated:
                            next_val = 0.0
                        else:
                            next_val = V[next_s_idx]
                        
                        q_val = reward + gamma * next_val
                        q_values.append(q_val)
                    
                    new_V[s_idx] = max(q_values)
                    delta = max(delta, abs(v_old - new_V[s_idx]))
            
            V = new_V
            if delta < threshold:
                break

        # Store the computed Q-values or Policy
        self.Q = np.zeros((total_states, n_actions))
        self.policy = np.zeros(total_states, dtype=int)

        # Re-run one pass to compute Q and Policy
        for grid_idx in range(n_grid_cells):
            for h_idx in range(n_hidden_states):
                s_idx = grid_idx * n_hidden_states + h_idx
                x = grid_idx // self.env.grid_size
                y = grid_idx % self.env.grid_size

                best_q = -np.inf
                best_a = 0

                for a in range(n_actions):
                    self.env.grid_pos = (x, y)
                    self.env.hidden_signal = h_idx
                    obs, reward, terminated, truncated, info = self.env.step(a)
                    next_grid_pos = self.env.grid_pos
                    next_hidden_signal = self.env.hidden_signal
                    
                    # Restore
                    self.env.grid_pos, self.env.hidden_signal = (x, y) # Wait, we need to restore to (x,y) before next iteration? 
                    # Actually, we are iterating, so we set it at the start of the loop.
                    # The step modified it. We must restore it to (x,y) for the next action?
                    # No, we set it to (x,y) at the start of the action loop.
                    # But the step modifies self.grid_pos.
                    # So we must restore it after reading next state.
                    
                    # Correction:
                    # 1. Set env to (x,y), h_idx
                    # 2. Step
                    # 3. Read next state
                    # 4. Restore env to (x,y), h_idx
                    
                    # Let's redo the logic cleanly inside the loop
                    self.env.grid_pos = (x, y)
                    self.env.hidden_signal = h_idx
                    obs, reward, terminated, truncated, info = self.env.step(a)
                    next_grid_pos = self.env.grid_pos
                    next_hidden_signal = self.env.hidden_signal
                    self.env.grid_pos, self.env.hidden_signal = (x, y), h_idx # Restore
                    
                    next_grid_idx = next_grid_pos[0] * self.env.grid_size + next_grid_pos[1]
                    next_s_idx = next_grid_idx * n_hidden_states + next_hidden_signal
                    
                    if terminated or truncated:
                        next_val = 0.0
                    else:
                        next_val = V[next_s_idx]
                    
                    q_val = reward + self.env.gamma * next_val
                    self.Q[s_idx, a] = q_val
                    
                    if q_val > best_q:
                        best_q = q_val
                        best_a = a
                
                self.policy[s_idx] = best_a

    def get_action(self, obs: np.ndarray, hidden_state: Optional[int] = None) -> int:
        """
        Returns the optimal action given the observation and the hidden state.
        
        Args:
            obs: The observable state O (grid position).
            hidden_state: The privileged state H.
            
        Returns:
            The optimal action index.
        """
        if hidden_state is None:
            raise ValueError("Teacher requires the hidden state H to act optimally.")
        
        # Convert obs to grid index
        # obs is likely (x, y) or an integer representing grid position.
        # PrivilegeMDP observation space is likely Box or Discrete representing grid.
        # Let's assume obs is a tuple (x, y) or we can derive the index.
        
        if isinstance(obs, tuple):
            grid_idx = obs[0] * self.env.grid_size + obs[1]
        elif isinstance(obs, np.ndarray):
            # If it's a flattened array or single value
            if obs.ndim == 0:
                grid_idx = int(obs)
            else:
                # Assume it's (x, y)
                grid_idx = int(obs[0]) * self.env.grid_size + int(obs[1])
        else:
            grid_idx = int(obs)
        
        s_idx = grid_idx * self.env.hidden_signal_levels + hidden_state
        return int(self.policy[s_idx])

    def get_q_value(self, obs: np.ndarray, hidden_state: int, action: int) -> float:
        """
        Returns the Q-value for a specific state-action pair.
        """
        if isinstance(obs, tuple):
            grid_idx = obs[0] * self.env.grid_size + obs[1]
        elif isinstance(obs, np.ndarray):
            if obs.ndim == 0:
                grid_idx = int(obs)
            else:
                grid_idx = int(obs[0]) * self.env.grid_size + int(obs[1])
        else:
            grid_idx = int(obs)
        
        s_idx = grid_idx * self.env.hidden_signal_levels + hidden_state
        return float(self.Q[s_idx, action])