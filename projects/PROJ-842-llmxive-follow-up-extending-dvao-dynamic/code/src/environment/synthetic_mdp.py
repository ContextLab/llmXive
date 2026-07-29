import numpy as np
from typing import Tuple, Dict, Optional, List, Any
import json
import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SyntheticTabularMDP:
    """
    Synthetic Tabular MDP for Multi-Objective Reinforcement Learning.
    
    Attributes:
        n_states (int): Number of states |S|.
        n_actions (int): Number of actions |A|.
        n_objectives (int): Number of objectives N.
        transition_matrix (np.ndarray): Shape (n_states, n_actions, n_states).
        reward_functions (List[np.ndarray]): List of reward matrices, one per objective.
        noise_correlation (float): Correlation parameter rho.
        noise_distribution (str): Type of noise distribution ('gaussian', 'heavy_tailed').
        dof (int): Degrees of freedom for Student's t distribution (if heavy_tailed).
        seed (int): Random seed for reproducibility.
        metadata (Dict): Additional metadata about the MDP.
    """
    n_states: int
    n_actions: int
    n_objectives: int
    transition_matrix: np.ndarray
    reward_functions: List[np.ndarray]
    noise_correlation: float = 0.0
    noise_distribution: str = 'gaussian'
    dof: int = 3
    seed: int = 42
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert MDP to a dictionary representation."""
        return {
            'n_states': self.n_states,
            'n_actions': self.n_actions,
            'n_objectives': self.n_objectives,
            'noise_correlation': self.noise_correlation,
            'noise_distribution': self.noise_distribution,
            'dof': self.dof,
            'seed': self.seed,
            'metadata': self.metadata
        }

def _generate_correlated_noise(
    n_states: int,
    n_actions: int,
    n_objectives: int,
    rho: float,
    rng: np.random.Generator,
    noise_distribution: str = 'gaussian',
    dof: int = 3
) -> np.ndarray:
    """
    Generate noise with specified correlation structure and distribution.
    
    Args:
        n_states: Number of states.
        n_actions: Number of actions.
        n_objectives: Number of objectives.
        rho: Correlation coefficient between objectives.
        rng: numpy random generator.
        noise_distribution: 'gaussian' or 'heavy_tailed'.
        dof: Degrees of freedom for Student's t (if heavy_tailed).
        
    Returns:
        np.ndarray: Noise tensor of shape (n_states, n_actions, n_objectives).
    """
    if rho < 0 or rho > 1:
        raise ValueError(f"Correlation coefficient rho must be in [0, 1], got {rho}")

    # Generate independent noise components
    if noise_distribution == 'heavy_tailed':
        # Student's t distribution with specified degrees of freedom
        # Standardize to have mean 0 and variance 1 for consistency
        # For t-distribution with dof > 2, variance is dof / (dof - 2)
        # We scale to unit variance
        scale_factor = np.sqrt((dof - 2) / dof)
        base_noise = rng.standard_t(dof, size=(n_states, n_actions, n_objectives)) * scale_factor
    else:
        # Gaussian noise
        base_noise = rng.standard_normal(size=(n_states, n_actions, n_objectives))

    if rho == 0:
        # No correlation: return independent noise
        return base_noise

    # Create correlated noise using Cholesky decomposition
    # Covariance matrix for objectives with correlation rho
    # Sigma = (1-rho)*I + rho*J where J is all-ones matrix
    cov_matrix = np.eye(n_objectives) * (1 - rho) + rho
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # Fallback for numerical issues
        logger.warning("Cholesky decomposition failed, using independent noise")
        return base_noise

    # Reshape base_noise for matrix multiplication
    # base_noise: (n_states, n_actions, n_objectives)
    # L: (n_objectives, n_objectives)
    # We want to multiply the last dimension by L
    n_samples = n_states * n_actions
    base_noise_flat = base_noise.reshape(n_samples, n_objectives)
    correlated_noise_flat = base_noise_flat @ L.T
    correlated_noise = correlated_noise_flat.reshape(n_states, n_actions, n_objectives)

    return correlated_noise

def generate_mdp(
    n_objectives: int = 5,
    n_states: Optional[int] = None,
    n_actions: int = 4,
    noise_correlation: float = 0.0,
    seed: int = 42,
    noise_distribution: str = 'gaussian',
    dof: int = 3,
    force_reduce_state_space: bool = False
) -> SyntheticTabularMDP:
    """
    Generate a synthetic tabular MDP with N objectives.
    
    Args:
        n_objectives: Number of objectives N.
        n_states: Number of states |S|. If None, defaults to 10 * n_objectives.
        n_actions: Number of actions |A|.
        noise_correlation: Correlation parameter rho ∈ [0, 1].
        seed: Random seed for reproducibility.
        noise_distribution: Type of noise distribution ('gaussian', 'heavy_tailed').
        dof: Degrees of freedom for Student's t distribution (if heavy_tailed).
        force_reduce_state_space: If True and N > 50, reduce state space size.
        
    Returns:
        SyntheticTabularMDP: Generated MDP instance.
    """
    rng = np.random.default_rng(seed)
    
    # State space degradation for large N (FR-016)
    if n_states is None:
        n_states = 10 * n_objectives
    
    if n_objectives > 50 and force_reduce_state_space:
        original_n_states = n_states
        n_states = n_states // 2
        logger.warning(f"State space reduced to {n_states} for memory constraints (N={n_objectives})")
    
    # Validate parameters
    if n_objectives <= 0:
        raise ValueError("n_objectives must be positive")
    if n_states <= 0:
        raise ValueError("n_states must be positive")
    if n_actions <= 0:
        raise ValueError("n_actions must be positive")
    
    # Generate transition probabilities (random stochastic matrix)
    transition_raw = rng.random((n_states, n_actions, n_states))
    transition_matrix = transition_raw / transition_raw.sum(axis=2, keepdims=True)
    
    # Generate reward functions with noise
    # Base rewards: random linear combinations of state features
    state_features = rng.random((n_states, n_objectives))
    reward_functions = []
    
    for i in range(n_objectives):
        # Create reward function for objective i
        # Add noise with specified correlation structure
        base_reward = state_features[:, i]
        
        # Generate correlated noise for this objective
        noise = _generate_correlated_noise(
            n_states, n_actions, n_objectives,
            noise_correlation, rng, noise_distribution, dof
        )
        
        # Extract noise for this objective
        objective_noise = noise[:, :, i]
        
        # Create reward matrix: (n_states, n_actions)
        reward_matrix = np.zeros((n_states, n_actions))
        for s in range(n_states):
            for a in range(n_actions):
                reward_matrix[s, a] = base_reward[s] + objective_noise[s, a]
        
        reward_functions.append(reward_matrix)
    
    # Create metadata
    metadata = {
        'generation_seed': seed,
        'noise_distribution': noise_distribution,
        'degrees_of_freedom': dof if noise_distribution == 'heavy_tailed' else None,
        'correlation_parameter': noise_correlation
    }
    
    if n_objectives > 50:
        metadata['state_space_reduced'] = n_objectives > 50
        metadata['original_n_states'] = original_n_states if n_objectives > 50 else None
        metadata['effective_n_states'] = n_states
    
    return SyntheticTabularMDP(
        n_states=n_states,
        n_actions=n_actions,
        n_objectives=n_objectives,
        transition_matrix=transition_matrix,
        reward_functions=reward_functions,
        noise_correlation=noise_correlation,
        noise_distribution=noise_distribution,
        dof=dof,
        seed=seed,
        metadata=metadata
    )

def generate_heavy_tailed_mdp(
    n_objectives: int = 5,
    n_states: Optional[int] = None,
    n_actions: int = 4,
    noise_correlation: float = 0.0,
    seed: int = 42,
    dof: int = 3,
    force_reduce_state_space: bool = False
) -> SyntheticTabularMDP:
    """
    Generate a synthetic tabular MDP with heavy-tailed noise distribution (Student's t).
    
    This function implements FR-012 and US-4 requirements for held-out set generation
    with heavy-tailed noise distribution.
    
    Args:
        n_objectives: Number of objectives N.
        n_states: Number of states |S|. If None, defaults to 10 * n_objectives.
        n_actions: Number of actions |A|.
        noise_correlation: Correlation parameter rho ∈ [0, 1].
        seed: Random seed for reproducibility (default 42 as per task spec).
        dof: Degrees of freedom for Student's t distribution (default 3).
        force_reduce_state_space: If True and N > 50, reduce state space size.
        
    Returns:
        SyntheticTabularMDP: Generated MDP instance with heavy-tailed noise.
        
    Raises:
        ValueError: If dof <= 2 (variance undefined for Student's t).
    """
    if dof <= 2:
        raise ValueError(f"Degrees of freedom must be > 2 for finite variance, got {dof}")
    
    logger.info(f"Generating heavy-tailed MDP with N={n_objectives}, dof={dof}, seed={seed}")
    
    mdp = generate_mdp(
        n_objectives=n_objectives,
        n_states=n_states,
        n_actions=n_actions,
        noise_correlation=noise_correlation,
        seed=seed,
        noise_distribution='heavy_tailed',
        dof=dof,
        force_reduce_state_space=force_reduce_state_space
    )
    
    # Verify noise distribution parameters
    if mdp.noise_distribution != 'heavy_tailed':
        raise RuntimeError("Failed to set noise distribution to heavy_tailed")
    if mdp.dof != dof:
        raise RuntimeError(f"Failed to set degrees of freedom to {dof}")
    
    logger.info(f"MDP generated successfully: {mdp.n_states} states, {mdp.n_actions} actions, {mdp.n_objectives} objectives")
    
    return mdp

def main():
    """CLI entry point for MDP generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic tabular MDP')
    parser.add_argument('--n-objectives', type=int, default=5, help='Number of objectives')
    parser.add_argument('--n-states', type=int, default=None, help='Number of states')
    parser.add_argument('--n-actions', type=int, default=4, help='Number of actions')
    parser.add_argument('--noise-correlation', type=float, default=0.0, help='Noise correlation parameter')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--heavy-tailed', action='store_true', help='Use heavy-tailed noise distribution')
    parser.add_argument('--dof', type=int, default=3, help='Degrees of freedom for heavy-tailed distribution')
    parser.add_argument('--output', type=str, default=None, help='Output JSON file path')
    
    args = parser.parse_args()
    
    if args.heavy_tailed:
        mdp = generate_heavy_tailed_mdp(
            n_objectives=args.n_objectives,
            n_states=args.n_states,
            n_actions=args.n_actions,
            noise_correlation=args.noise_correlation,
            seed=args.seed,
            dof=args.dof
        )
    else:
        mdp = generate_mdp(
            n_objectives=args.n_objectives,
            n_states=args.n_states,
            n_actions=args.n_actions,
            noise_correlation=args.noise_correlation,
            seed=args.seed
        )
    
    # Output MDP metadata
    print(json.dumps(mdp.to_dict(), indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(mdp.to_dict(), f, indent=2)
        print(f"MDP metadata saved to {args.output}")

if __name__ == '__main__':
    main()
