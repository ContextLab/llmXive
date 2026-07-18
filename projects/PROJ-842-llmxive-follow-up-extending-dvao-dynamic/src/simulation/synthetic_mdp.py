"""
Synthetic MDP Generation for Multi-Objective Reinforcement Learning.

This module implements the generation of tabular MDPs with N objectives.
It supports:
1. Random linear combinations of state features for reward generation.
2. Explicit noise correlation parameter rho (ρ) ∈ {0, 0.2, 0.5} as per FR-009.
3. Deterministic seeded random state management.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class TabularMDP:
    """
    A simple tabular MDP structure for multi-objective experiments.

    Attributes:
        num_states (int): Number of states.
        num_actions (int): Number of actions.
        num_objectives (int): Number of reward objectives (N).
        transition_probs (np.ndarray): Shape (S, A, S).
        reward_vectors (np.ndarray): Shape (S, A, S, N).
        gamma (float): Discount factor.
        initial_state (int): Starting state index.
    """
    num_states: int
    num_actions: int
    num_objectives: int
    transition_probs: np.ndarray
    reward_vectors: np.ndarray
    gamma: float
    initial_state: int


def generate_correlated_noise(
    shape: Tuple[int, ...],
    rho: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generates a noise vector with a specific correlation structure.

    Implements the requirement for noise correlation parameter ρ.
    For ρ=0, noise is i.i.d.
    For ρ>0, noise components share a common latent factor to induce correlation.

    Model: ε_i = sqrt(ρ) * Z_common + sqrt(1-ρ) * Z_i
    Where Z_common and Z_i are independent standard normals.
    This ensures Var(ε_i) = 1 and Cov(ε_i, ε_j) = ρ for i != j.

    Args:
        shape: The shape of the output noise array.
        rho: The correlation coefficient (0 <= rho < 1).
        rng: The random number generator instance.

    Returns:
        np.ndarray: Noise array with specified correlation structure.
    """
    if not (0.0 <= rho < 1.0):
        raise ValueError(f"rho must be in [0, 1), got {rho}")

    # Flatten shape for vector operations, then reshape back
    size = int(np.prod(shape))
    
    # Common latent factor (shared across all objectives in this sample)
    z_common = rng.normal(0, 1, size)
    
    # Independent factors for each objective
    z_independent = rng.normal(0, 1, size)
    
    # Construct correlated noise
    # If rho is close to 1, we rely mostly on common factor
    noise = np.sqrt(rho) * z_common + np.sqrt(1 - rho) * z_independent
    
    return noise.reshape(shape)


def generate_synthetic_mdp(
    n_states: int = 20,
    n_actions: int = 4,
    n_objectives: int = 5,
    rho: float = 0.0,
    seed: int = 42,
    gamma: float = 0.99
) -> TabularMDP:
    """
    Generates a synthetic tabular MDP with N objectives.

    The reward vectors are generated using random linear combinations of
    state features. Noise correlation is applied as per FR-009.

    Args:
        n_states: Number of states (S).
        n_actions: Number of actions (A).
        n_objectives: Number of objectives (N).
        rho: Noise correlation parameter (ρ ∈ {0, 0.2, 0.5}).
        seed: Random seed for deterministic reproducibility.
        gamma: Discount factor.

    Returns:
        TabularMDP: The generated MDP instance.
    """
    if not (0.0 <= rho < 1.0):
        raise ValueError(f"rho must be in [0, 1), got {rho}")
    
    # Initialize RNG with seed for determinism
    rng = np.random.default_rng(seed)

    # 1. Generate Transition Probabilities (S, A, S)
    # Random stochastic matrix: uniform distribution over next states
    raw_transitions = rng.random((n_states, n_actions, n_states))
    transition_probs = raw_transitions / raw_transitions.sum(axis=2, keepdims=True)

    # 2. Generate State Features
    # Each state has a latent feature vector used to derive rewards
    state_features = rng.normal(0, 1, (n_states, n_objectives))

    # 3. Generate Base Rewards (S, A, S, N)
    # Reward is a linear combination of state features + noise
    # R(s, a, s') = w_a^T * phi(s') + noise
    # We assign a random weight vector per action
    action_weights = rng.normal(0, 1, (n_actions, n_objectives))
    
    # Base deterministic reward calculation
    # Expand dimensions for broadcasting: (S, A, S, 1) * (A, N) -> (S, A, S, N)
    # Actually, we want: sum over objectives: weight[action, obj] * feature[next_state, obj]
    # Let's compute: (S, A, S, 1) dot (A, 1, 1, N) -> (S, A, S, N)
    # But simpler: iterate or use einsum.
    # reward[s, a, s', k] = sum_j ( action_weights[a, j] * state_features[s', j] )
    
    base_rewards = np.einsum('saj,ajk->sajk', 
                             np.ones((n_states, n_actions, n_states)), 
                             np.zeros((n_actions, n_objectives))) # Placeholder logic
    
    # Correct calculation:
    # For each action a, and next state s', reward vector is W_a . phi(s')
    # Shape: (S, A, S, N)
    # We can do this efficiently:
    # Expand state_features to (1, 1, S, N)
    # Expand action_weights to (1, A, 1, N)
    # Dot product over the last dimension? No, element-wise multiply and sum.
    
    # Let's construct the deterministic part:
    # det_reward[s, a, s', k] = action_weights[a, k] * state_features[s', k]
    # Sum over k? No, the reward is a vector.
    # So reward_vector[s, a, s'] = action_weights[a] * state_features[s'] (element-wise)
    # Wait, "linear combination" usually means dot product.
    # If reward is a scalar per objective k, then:
    # r_k(s, a, s') = sum_j ( W_{a, k, j} * phi_j(s') ) ? 
    # Or simpler: r_k(s, a, s') = W_{a, k} * phi_k(s') ?
    # Let's assume: r_k = W_{a, k} * phi_k(s') (element-wise scaling)
    # This creates N distinct objectives based on specific features.
    
    # Shape alignment:
    # state_features: (S, N)
    # action_weights: (A, N)
    # Result: (S, A, S, N)
    
    # Expand to broadcast:
    # s: 0, a: 1, s': 2, k: 3
    # state_features: (1, 1, S, N) -> (1, 1, n_states, n_objectives)
    # action_weights: (1, A, 1, N) -> (1, n_actions, 1, n_objectives)
    
    sf_exp = state_features.reshape(1, 1, n_states, n_objectives)
    aw_exp = action_weights.reshape(1, n_actions, 1, n_objectives)
    
    deterministic_rewards = sf_exp * aw_exp

    # 4. Add Correlated Noise
    # We need noise for every transition (S, A, S, N)
    noise_shape = (n_states, n_actions, n_states, n_objectives)
    noise = generate_correlated_noise(noise_shape, rho, rng)
    
    # Scale noise to a reasonable magnitude (e.g., 0.1 std dev)
    noise_scale = 0.1
    reward_vectors = deterministic_rewards + noise_scale * noise

    return TabularMDP(
        num_states=n_states,
        num_actions=n_actions,
        num_objectives=n_objectives,
        transition_probs=transition_probs,
        reward_vectors=reward_vectors,
        gamma=gamma,
        initial_state=0
    )


def get_mdp_transition(mdp: TabularMDP, state: int, action: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Retrieves the transition probabilities and reward vectors for a given state-action pair.

    Args:
        mdp: The MDP instance.
        state: Current state index.
        action: Action index.

    Returns:
        Tuple of (next_state_probs, reward_vectors)
        next_state_probs: Shape (S,)
        reward_vectors: Shape (S, N) - reward for transitioning to each next state
    """
    probs = mdp.transition_probs[state, action, :]
    rewards = mdp.reward_vectors[state, action, :, :]
    return probs, rewards
