import numpy as np
from typing import Tuple, Dict, Optional, List, Any
import json
import os
import logging
from dataclasses import dataclass, field

from src.config.defaults import load_config, get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SyntheticTabularMDP:
    """
    Synthetic Tabular MDP for Multi-Objective Reinforcement Learning.
    
    Attributes:
        n_states: Number of states |S|
        n_actions: Number of actions |A|
        n_objectives: Number of reward objectives N
        transition_matrix: P(s'|s, a) shape (n_states, n_actions, n_states)
        reward_matrices: List of reward matrices R(s, a) shape (n_objectives, n_states, n_actions)
        noise_correlation: Correlation parameter rho
        distribution_type: Type of reward distribution ('linear', 'sparse', 'non_convex', 'heavy_tailed')
        metadata: Additional metadata
    """
    n_states: int
    n_actions: int
    n_objectives: int
    transition_matrix: np.ndarray
    reward_matrices: List[np.ndarray]
    noise_correlation: float = 0.0
    distribution_type: str = 'linear'
    seed: int = 42
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_reward(self, s: int, a: int, objective_idx: int) -> float:
        """Get reward for state-action pair on specific objective."""
        return self.reward_matrices[objective_idx][s, a]

    def get_all_rewards(self, s: int, a: int) -> np.ndarray:
        """Get reward vector for state-action pair across all objectives."""
        return np.array([R[s, a] for R in self.reward_matrices])

    def calculate_sparsity_ratio(self) -> float:
        """Calculate the sparsity ratio of the reward matrices."""
        total_elements = sum(R.size for R in self.reward_matrices)
        non_zero_elements = sum(np.count_nonzero(R) for R in self.reward_matrices)
        return non_zero_elements / total_elements if total_elements > 0 else 0.0

    def calculate_non_convexity_metric(self) -> float:
        """
        Calculate a non-convexity metric for the reward landscape.
        This measures the deviation from linearity in the reward space.
        """
        if self.n_objectives < 2:
            return 0.0
        
        # Sample a subset of state-action pairs to compute curvature
        sample_size = min(100, self.n_states * self.n_actions)
        indices = np.random.choice(self.n_states * self.n_actions, sample_size, replace=False)
        
        curvature_scores = []
        for idx in indices:
            s = idx // self.n_actions
            a = idx % self.n_actions
            
            # Get reward vector
            r_vec = self.get_all_rewards(s, a)
            
            # Compute local curvature by comparing to neighbors
            # If neighbors exist, compute variance of reward differences
            neighbors = []
            for ds in [-1, 1]:
                for da in [-1, 1]:
                    ns, na = s + ds, a + da
                    if 0 <= ns < self.n_states and 0 <= na < self.n_actions:
                        neighbors.append(self.get_all_rewards(ns, na))
            
            if len(neighbors) > 0:
                neighbor_matrix = np.array(neighbors)
                # Curvature: variance of differences from center
                diffs = neighbor_matrix - r_vec
                curvature = np.mean(np.var(diffs, axis=0))
                curvature_scores.append(curvature)
        
        return np.mean(curvature_scores) if curvature_scores else 0.0

def generate_mdp(
    n_objectives: int,
    n_states: Optional[int] = None,
    n_actions: Optional[int] = None,
    noise_correlation: float = 0.0,
    seed: int = 42,
    distribution_type: str = 'linear'
) -> SyntheticTabularMDP:
    """
    Generate a synthetic tabular MDP with specified parameters.
    
    Args:
        n_objectives: Number of reward objectives
        n_states: Number of states (default: 10 * n_objectives)
        n_actions: Number of actions (default: 5)
        noise_correlation: Correlation parameter rho ∈ [0, 1]
        seed: Random seed for reproducibility
        distribution_type: Type of reward distribution ('linear', 'sparse', 'non_convex')
    
    Returns:
        SyntheticTabularMDP instance
    """
    np.random.seed(seed)
    
    if n_states is None:
        # Reduce state space for N > 50 to handle memory constraints
        if n_objectives > 50:
            n_states = max(10, 1000 // n_objectives)
            logger.warning(f"State space reduced to {n_states} for memory constraints (N={n_objectives})")
        else:
            n_states = max(10, 10 * n_objectives)
    
    if n_actions is None:
        n_actions = 5
    
    # Generate transition matrix
    transition_matrix = np.random.rand(n_states, n_actions, n_states)
    transition_matrix = transition_matrix / transition_matrix.sum(axis=2, keepdims=True)
    
    # Generate reward matrices based on distribution type
    reward_matrices = []
    
    if distribution_type == 'linear':
        # Linear combination of state features
        for _ in range(n_objectives):
            reward_matrix = np.random.randn(n_states, n_actions)
            reward_matrices.append(reward_matrix)
    
    elif distribution_type == 'sparse':
        # Sparse rewards: >90% zeros
        for _ in range(n_objectives):
            reward_matrix = np.random.randn(n_states, n_actions)
            # Apply sparsity mask (keep ~10% non-zero)
            sparsity_mask = np.random.rand(n_states, n_actions) > 0.9
            reward_matrix = reward_matrix * sparsity_mask
            reward_matrices.append(reward_matrix)
    
    elif distribution_type == 'non_convex':
        # Non-convex rewards: high curvature
        for _ in range(n_objectives):
            # Create a base linear reward
            base_reward = np.random.randn(n_states, n_actions)
            
            # Add non-linear perturbations
            s_coords = np.arange(n_states).reshape(-1, 1)
            a_coords = np.arange(n_actions).reshape(1, -1)
            
            # Quadratic and sinusoidal components for non-convexity
            non_linear = (
                0.5 * (s_coords ** 2) / n_states +
                0.3 * np.sin(2 * np.pi * a_coords / n_actions) * (s_coords / n_states) +
                0.2 * np.random.randn(n_states, n_actions)
            )
            
            reward_matrix = base_reward + non_linear
            reward_matrices.append(reward_matrix)
    
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")
    
    # Apply noise correlation if specified
    if noise_correlation > 0 and n_objectives > 1:
        # Create correlated noise across objectives
        for i in range(n_objectives):
            for j in range(i + 1, n_objectives):
                # Mix rewards to introduce correlation
                mix_factor = noise_correlation
                reward_matrices[i] = (1 - mix_factor) * reward_matrices[i] + mix_factor * reward_matrices[j]
                reward_matrices[j] = (1 - mix_factor) * reward_matrices[j] + mix_factor * reward_matrices[i]
    
    mdp = SyntheticTabularMDP(
        n_states=n_states,
        n_actions=n_actions,
        n_objectives=n_objectives,
        transition_matrix=transition_matrix,
        reward_matrices=reward_matrices,
        noise_correlation=noise_correlation,
        distribution_type=distribution_type,
        seed=seed,
        metadata={
            'generated_at': str(np.random.get_state()[1][0]),
            'distribution_type': distribution_type,
            'sparsity_ratio': None,
            'non_convexity_metric': None
        }
    )
    
    # Calculate and store metrics
    if distribution_type == 'sparse':
        mdp.metadata['sparsity_ratio'] = mdp.calculate_sparsity_ratio()
        logger.info(f"Generated Sparse MDP with sparsity ratio: {mdp.metadata['sparsity_ratio']:.4f}")
        assert mdp.metadata['sparsity_ratio'] > 0.9, f"Sparsity ratio {mdp.metadata['sparsity_ratio']} is not > 0.9"
    
    elif distribution_type == 'non_convex':
        mdp.metadata['non_convexity_metric'] = mdp.calculate_non_convexity_metric()
        logger.info(f"Generated Non-Convex MDP with curvature metric: {mdp.metadata['non_convexity_metric']:.4f}")
        assert mdp.metadata['non_convexity_metric'] > 0.5, f"Non-convexity metric {mdp.metadata['non_convexity_metric']} is not > 0.5"
    
    return mdp

def generate_sparse_mdp(
    n_objectives: int,
    n_states: Optional[int] = None,
    n_actions: Optional[int] = None,
    noise_correlation: float = 0.0,
    seed: int = 42
) -> SyntheticTabularMDP:
    """
    Generate a synthetic MDP with sparse reward distribution.
    
    Args:
        n_objectives: Number of reward objectives
        n_states: Number of states (default: auto-calculated)
        n_actions: Number of actions (default: 5)
        noise_correlation: Correlation parameter rho
        seed: Random seed
    
    Returns:
        SyntheticTabularMDP instance with sparse rewards (>90% zeros)
    """
    return generate_mdp(
        n_objectives=n_objectives,
        n_states=n_states,
        n_actions=n_actions,
        noise_correlation=noise_correlation,
        seed=seed,
        distribution_type='sparse'
    )

def generate_nonconvex_mdp(
    n_objectives: int,
    n_states: Optional[int] = None,
    n_actions: Optional[int] = None,
    noise_correlation: float = 0.0,
    seed: int = 42
) -> SyntheticTabularMDP:
    """
    Generate a synthetic MDP with non-convex reward distribution.
    
    Args:
        n_objectives: Number of reward objectives
        n_states: Number of states (default: auto-calculated)
        n_actions: Number of actions (default: 5)
        noise_correlation: Correlation parameter rho
        seed: Random seed
    
    Returns:
        SyntheticTabularMDP instance with non-convex rewards (curvature > 0.5)
    """
    return generate_mdp(
        n_objectives=n_objectives,
        n_states=n_states,
        n_actions=n_actions,
        noise_correlation=noise_correlation,
        seed=seed,
        distribution_type='non_convex'
    )

def generate_linear_mdp(
    n_objectives: int,
    n_states: Optional[int] = None,
    n_actions: Optional[int] = None,
    noise_correlation: float = 0.0,
    seed: int = 42
) -> SyntheticTabularMDP:
    """
    Generate a synthetic MDP with linear reward distribution (baseline).
    
    Args:
        n_objectives: Number of reward objectives
        n_states: Number of states (default: auto-calculated)
        n_actions: Number of actions (default: 5)
        noise_correlation: Correlation parameter rho
        seed: Random seed
    
    Returns:
        SyntheticTabularMDP instance with linear rewards
    """
    return generate_mdp(
        n_objectives=n_objectives,
        n_states=n_states,
        n_actions=n_actions,
        noise_correlation=noise_correlation,
        seed=seed,
        distribution_type='linear'
    )

def main():
    """CLI entry point for testing MDP generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic MDPs')
    parser.add_argument('--n-objectives', type=int, default=5, help='Number of objectives')
    parser.add_argument('--n-states', type=int, default=None, help='Number of states')
    parser.add_argument('--n-actions', type=int, default=5, help='Number of actions')
    parser.add_argument('--noise-correlation', type=float, default=0.0, help='Noise correlation rho')
    parser.add_argument('--distribution', type=str, default='linear', 
                      choices=['linear', 'sparse', 'non_convex'],
                      help='Reward distribution type')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    logger.info(f"Generating {args.distribution} MDP with N={args.n_objectives} objectives...")
    
    if args.distribution == 'sparse':
        mdp = generate_sparse_mdp(
            n_objectives=args.n_objectives,
            n_states=args.n_states,
            n_actions=args.n_actions,
            noise_correlation=args.noise_correlation,
            seed=args.seed
        )
    elif args.distribution == 'non_convex':
        mdp = generate_nonconvex_mdp(
            n_objectives=args.n_objectives,
            n_states=args.n_states,
            n_actions=args.n_actions,
            noise_correlation=args.noise_correlation,
            seed=args.seed
        )
    else:
        mdp = generate_linear_mdp(
            n_objectives=args.n_objectives,
            n_states=args.n_states,
            n_actions=args.n_actions,
            noise_correlation=args.noise_correlation,
            seed=args.seed
        )
    
    logger.info(f"MDP generated: |S|={mdp.n_states}, |A|={mdp.n_actions}, N={mdp.n_objectives}")
    logger.info(f"Distribution: {mdp.distribution_type}")
    
    if mdp.distribution_type == 'sparse':
        logger.info(f"Sparsity ratio: {mdp.metadata['sparsity_ratio']:.4f}")
    elif mdp.distribution_type == 'non_convex':
        logger.info(f"Non-convexity metric: {mdp.metadata['non_convexity_metric']:.4f}")
    
    # Save metadata to data/processed
    os.makedirs('data/processed', exist_ok=True)
    output_path = f'data/processed/{args.distribution}_mdp_{args.n_objectives}.json'
    with open(output_path, 'w') as f:
        json.dump({
            'n_states': mdp.n_states,
            'n_actions': mdp.n_actions,
            'n_objectives': mdp.n_objectives,
            'distribution_type': mdp.distribution_type,
            'noise_correlation': mdp.noise_correlation,
            'seed': mdp.seed,
            'metadata': mdp.metadata
        }, f, indent=2)
    
    logger.info(f"Metadata saved to {output_path}")
    
    return mdp

if __name__ == '__main__':
    main()
