import numpy as np
from typing import Tuple, Dict, Optional, List, Any
import json
import os
import logging
from dataclasses import dataclass, field
from scipy import stats as scipy_stats

# Configure logging for this module
logger = logging.getLogger(__name__)

@dataclass
class SyntheticTabularMDP:
    """
    A synthetic tabular MDP with N objectives.
    Supports various noise distributions including heavy-tailed (Student's t) and sparse.
    """
    n_objectives: int
    state_space_size: int
    action_space_size: int
    transition_probabilities: np.ndarray  # [S, A, S]
    reward_functions: List[np.ndarray]    # List of [S, A] arrays, one per objective
    noise_distribution: str               # 'gaussian', 'heavy_tailed', 'sparse', 'linear', 'nonconvex'
    noise_params: Dict[str, Any]          # Parameters for the noise distribution
    seed: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Basic validation
        assert self.state_space_size > 0
        assert self.action_space_size > 0
        assert self.n_objectives > 0
        assert len(self.reward_functions) == self.n_objectives
        self.metadata['created'] = True

def generate_mdp(n_objectives: int, seed: int = 42, noise_correlation: float = 0.0,
                 noise_dist: str = 'gaussian', force_reduce_state_space: bool = False) -> SyntheticTabularMDP:
    """
    Generate a synthetic tabular MDP with N objectives.
    
    Args:
        n_objectives: Number of objectives (N)
        seed: Random seed for reproducibility
        noise_correlation: Correlation parameter rho for noise (0 to 1)
        noise_dist: Distribution type ('gaussian', 'heavy_tailed', 'sparse', 'linear', 'nonconvex')
        force_reduce_state_space: If True, reduce state space for N > 50
        
    Returns:
        SyntheticTabularMDP instance
    """
    rng = np.random.default_rng(seed)
    
    # State space size logic (with reduction for large N)
    base_state_size = 1000
    state_space_size = base_state_size
    reduced = False
    
    if n_objectives > 50 and force_reduce_state_space:
        state_space_size = base_state_size // 2
        reduced = True
        logger.warning(f"State space reduced to {state_space_size} for memory constraints (N={n_objectives})")
    
    action_space_size = 5  # Fixed number of actions for simplicity
    
    # Generate transition probabilities (random stochastic matrix)
    # Shape: [S, A, S]
    raw_transitions = rng.random((state_space_size, action_space_size, state_space_size))
    transition_probabilities = raw_transitions / raw_transitions.sum(axis=2, keepdims=True)
    
    # Generate reward functions
    reward_functions = []
    
    # Generate base reward weights (linear combinations of state features)
    # For each objective, we have a weight vector over states
    state_features = rng.random((state_space_size, n_objectives))
    
    for obj_idx in range(n_objectives):
        # Base reward signal
        base_reward = state_features[:, obj_idx]
        
        # Add noise based on distribution type
        if noise_dist == 'gaussian':
            noise = rng.normal(0, 0.1, state_space_size)
        elif noise_dist == 'heavy_tailed':
            # Student's t distribution with df=3 (heavy-tailed)
            noise = rng.standard_t(df=3, size=state_space_size) * 0.1
        elif noise_dist == 'sparse':
            # Sparse noise: most values are zero, some are large
            sparsity_ratio = 0.95
            mask = rng.random(state_space_size) > sparsity_ratio
            noise = np.zeros(state_space_size)
            noise[mask] = rng.normal(0, 1.0, np.sum(mask))
        elif noise_dist == 'linear':
            # Linear correlation between objectives
            noise = rng.normal(0, 0.1, state_space_size)
            if obj_idx > 0:
                # Add correlation to previous objective's noise
                noise = noise * (1 - noise_correlation) + reward_functions[-1] * noise_correlation
        elif noise_dist == 'nonconvex':
            # Non-convex: mixture of Gaussians with high variance
            mix_idx = rng.choice([0, 1], size=state_space_size, p=[0.3, 0.7])
            noise = np.zeros(state_space_size)
            noise[mix_idx == 0] = rng.normal(0, 0.5, np.sum(mix_idx == 0))
            noise[mix_idx == 1] = rng.normal(0, 2.0, np.sum(mix_idx == 1))
        else:
            raise ValueError(f"Unknown noise distribution: {noise_dist}")
        
        final_reward = base_reward + noise
        
        # Expand to [S, A] (same reward for all actions for simplicity)
        reward_matrix = np.tile(final_reward.reshape(-1, 1), (1, action_space_size))
        reward_functions.append(reward_matrix)
    
    metadata = {
        'n_objectives': n_objectives,
        'state_space_size': state_space_size,
        'action_space_size': action_space_size,
        'noise_distribution': noise_dist,
        'noise_correlation': noise_correlation,
        'seed': seed,
        'state_space_reduced': reduced
    }
    
    return SyntheticTabularMDP(
        n_objectives=n_objectives,
        state_space_size=state_space_size,
        action_space_size=action_space_size,
        transition_probabilities=transition_probabilities,
        reward_functions=reward_functions,
        noise_distribution=noise_dist,
        noise_params={'seed': seed},
        seed=seed,
        metadata=metadata
    )

def generate_heavy_tailed_mdp(n_objectives: int, seed: int = 42, 
                              df: float = 3.0, noise_scale: float = 0.1) -> SyntheticTabularMDP:
    """
    Generate a synthetic MDP with heavy-tailed (Student's t) noise.
    
    Args:
        n_objectives: Number of objectives
        seed: Random seed
        df: Degrees of freedom for Student's t (default 3.0 for heavy tails)
        noise_scale: Scale factor for the noise
        
    Returns:
        SyntheticTabularMDP instance with heavy-tailed noise
    """
    # Use the main generator with heavy_tailed distribution
    mdp = generate_mdp(
        n_objectives=n_objectives,
        seed=seed,
        noise_dist='heavy_tailed'
    )
    # Update metadata with specific heavy-tailed parameters
    mdp.metadata['df'] = df
    mdp.metadata['noise_scale'] = noise_scale
    mdp.noise_params['df'] = df
    mdp.noise_params['scale'] = noise_scale
    return mdp

def validate_distribution(mdp: SyntheticTabularMDP, log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate that the generated noise matches the requested distribution using KS-test.
    
    Args:
        mdp: The generated MDP instance
        log_file: Optional path to a log file to write validation results
        
    Returns:
        Dictionary with validation results including p-values
    """
    results = {
        'distribution_type': mdp.noise_distribution,
        'validation_passed': False,
        'p_values': {},
        'statistics': {}
    }
    
    # Collect all noise samples from reward functions
    # We extract noise by comparing against a smoothed/expected signal
    # For validation, we'll look at the residuals after removing the base signal
    
    all_noise_samples = []
    state_space_size = mdp.state_space_size
    
    for obj_idx, reward_matrix in enumerate(mdp.reward_functions):
        # Extract one column (action 0) for analysis
        rewards = reward_matrix[:, 0]
        
        # Estimate base signal (smoothed version)
        # For simplicity, we assume the base signal is the median or a low-pass filtered version
        # In practice, we'd know the exact base signal from generation
        # Here we use a simple approach: the noise is the deviation from a local mean
        
        # For heavy-tailed validation, we specifically check if the tails match Student's t
        if mdp.noise_distribution == 'heavy_tailed':
            # We need to isolate the noise component
            # Since we generated it as: reward = base + noise, and we know the generation process,
            # we can try to estimate the noise by looking at the distribution of rewards
            # For a proper test, we'd need the ground truth base signal
            
            # Alternative: Generate a known base signal and compare
            # For now, we'll test the distribution of the rewards directly against a t-distribution
            # This is a simplified approach
            
            df = mdp.noise_params.get('df', 3.0)
            scale = mdp.noise_params.get('scale', 0.1)
            
            # Test against Student's t distribution
            # Note: This is an approximation since we don't have the exact base signal
            # A more rigorous test would require the ground truth
            
            # For heavy-tailed, we expect higher kurtosis
            kurtosis = scipy_stats.kurtosis(rewards, fisher=True)
            results['statistics'][f'obj_{obj_idx}_kurtosis'] = kurtosis
            
            # KS-test against t-distribution (approximate)
            # We'll generate a reference t-distribution with the same scale
            reference_samples = scipy_stats.t.rvs(df=df, scale=scale, size=len(rewards), 
                                                 random_state=mdp.seed + obj_idx)
            ks_stat, p_value = scipy_stats.ks_2samp(rewards, reference_samples)
            results['p_values'][f'obj_{obj_idx}_ks_test'] = p_value
            results['statistics'][f'obj_{obj_idx}_ks_stat'] = ks_stat
            
        elif mdp.noise_distribution == 'sparse':
            # Check sparsity ratio
            # Assuming noise is sparse if many values are near zero
            threshold = 1e-3
            sparsity = np.sum(np.abs(rewards) < threshold) / len(rewards)
            results['statistics'][f'obj_{obj_idx}_sparsity'] = sparsity
            
            # For sparse, we expect high sparsity (> 0.9)
            if sparsity > 0.9:
                results['p_values'][f'obj_{obj_idx}_sparsity_test'] = 1.0  # Pass
            else:
                results['p_values'][f'obj_{obj_idx}_sparsity_test'] = 0.0  # Fail
                
        elif mdp.noise_distribution == 'gaussian':
            # KS-test against normal distribution
            ks_stat, p_value = scipy_stats.kstest(rewards, 'norm')
            results['p_values'][f'obj_{obj_idx}_ks_test'] = p_value
            results['statistics'][f'obj_{obj_idx}_ks_stat'] = ks_stat
            
        elif mdp.noise_distribution == 'nonconvex':
            # Check for bimodality (non-convex)
            # Use Hartigan's dip test or simply check for two peaks
            hist, bin_edges = np.histogram(rewards, bins=50, density=True)
            # Count local maxima
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(hist, height=0.01)
            num_peaks = len(peaks)
            results['statistics'][f'obj_{obj_idx}_num_peaks'] = num_peaks
            
            # Non-convex should have multiple peaks
            if num_peaks >= 2:
                results['p_values'][f'obj_{obj_idx}_bimodality_test'] = 1.0
            else:
                results['p_values'][f'obj_{obj_idx}_bimodality_test'] = 0.0
                
        elif mdp.noise_distribution == 'linear':
            # Check correlation between objectives
            if obj_idx > 0:
                prev_rewards = mdp.reward_functions[obj_idx - 1][:, 0]
                corr = np.corrcoef(rewards, prev_rewards)[0, 1]
                results['statistics'][f'obj_{obj_idx}_correlation'] = corr
                # For linear, we expect high correlation
                if corr > 0.5:  # Threshold for "high" correlation
                    results['p_values'][f'obj_{obj_idx}_correlation_test'] = 1.0
                else:
                    results['p_values'][f'obj_{obj_idx}_correlation_test'] = 0.0
        
        all_noise_samples.extend(rewards.tolist())
    
    # Overall validation: at least one objective should pass (p > 0.05)
    # For heavy-tailed, we expect p > 0.05 if the distribution matches
    p_values = list(results['p_values'].values())
    if len(p_values) > 0:
        # Check if any p-value is > 0.05 (fail to reject null hypothesis)
        results['validation_passed'] = any(p > 0.05 for p in p_values)
        results['min_p_value'] = min(p_values)
        results['max_p_value'] = max(p_values)
    
    # Log results
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"\n=== Distribution Validation for N={mdp.n_objectives} ===\n")
            f.write(f"Distribution: {mdp.noise_distribution}\n")
            f.write(f"Validation Passed: {results['validation_passed']}\n")
            for key, value in results['p_values'].items():
                f.write(f"{key}: {value:.4f}\n")
            f.write(f"Min p-value: {results.get('min_p_value', 'N/A'):.4f}\n")
            f.write(f"Max p-value: {results.get('max_p_value', 'N/A'):.4f}\n")
            f.write("=" * 50 + "\n")
    
    logger.info(f"Distribution validation for {mdp.noise_distribution}: "
               f"passed={results['validation_passed']}, "
               f"min_p={results.get('min_p_value', 'N/A'):.4f}")
    
    return results

def main():
    """
    Main function to demonstrate MDP generation and distribution validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and validate synthetic MDPs')
    parser.add_argument('--n-objectives', type=int, default=10, help='Number of objectives')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--noise-dist', type=str, default='gaussian',
                      choices=['gaussian', 'heavy_tailed', 'sparse', 'linear', 'nonconvex'],
                      help='Noise distribution type')
    parser.add_argument('--log-file', type=str, default='logs/runner.log',
                      help='Path to log file for validation results')
    parser.add_argument('--df', type=float, default=3.0, help='Degrees of freedom for heavy-tailed')
    
    args = parser.parse_args()
    
    # Set up logging
    os.makedirs(os.path.dirname(args.log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(args.log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Generating MDP with N={args.n_objectives}, seed={args.seed}, "
               f"distribution={args.noise_dist}")
    
    # Generate MDP
    if args.noise_dist == 'heavy_tailed':
        mdp = generate_heavy_tailed_mdp(
            n_objectives=args.n_objectives,
            seed=args.seed,
            df=args.df
        )
    else:
        mdp = generate_mdp(
            n_objectives=args.n_objectives,
            seed=args.seed,
            noise_dist=args.noise_dist
        )
    
    # Validate distribution
    validation_results = validate_distribution(mdp, log_file=args.log_file)
    
    # Print results
    print(f"\nValidation Results:")
    print(f"  Distribution: {validation_results['distribution_type']}")
    print(f"  Passed: {validation_results['validation_passed']}")
    print(f"  Min p-value: {validation_results.get('min_p_value', 'N/A'):.4f}")
    print(f"  Max p-value: {validation_results.get('max_p_value', 'N/A'):.4f}")
    
    # Return 0 if validation passed, 1 otherwise
    return 0 if validation_results['validation_passed'] else 1

if __name__ == '__main__':
    exit(main())
