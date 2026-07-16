import argparse
import numpy as np
from typing import Dict, Any, List, Optional

# Constants from T004
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    np.random.seed(seed)

def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate configuration parameters.
    
    Args:
        cfg: Configuration dictionary.
        
    Raises:
        ValueError: If configuration is invalid.
    """
    if cfg['n_clusters'] < 50 and cfg['icc'] != 0.0:
        raise ValueError(f"n_clusters must be >= 50 when icc != 0.0, got {cfg['n_clusters']}")

def load_config() -> Dict[str, Any]:
    """Load default configuration.
    
    Returns:
        Default configuration dictionary.
    """
    return {
        'icc_range': ICC_RANGE.copy(),
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS.copy(),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'seed': DEFAULT_SEED,
        'n_obs_per_cluster': 100,  # Added for simulation runner
        'n_permutations': 1000,    # Added for permutation tests
        'output_baseline': 'data/derived/baseline_results.csv',
        'output_robust': 'data/derived/robustResults.csv',
    }

def parse_cli_args(args: Optional[argparse.Namespace] = None, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse command-line arguments and update configuration.
    
    This function is designed to be flexible and accept different call signatures:
    1. parse_cli_args() - Returns config with defaults
    2. parse_cli_args(args) - Parses args and returns new config
    3. parse_cli_args(args, cfg) - Parses args and updates existing config
    
    Args:
        args: argparse.Namespace from ArgumentParser.parse_args(). Can be None.
        cfg: Existing configuration dictionary to update. Can be None.
        
    Returns:
        Updated configuration dictionary.
        
    Raises:
        SystemExit: If CLI argument parsing fails.
    """
    # Initialize config if not provided
    if cfg is None:
        cfg = load_config()
    
    # If no args provided, just return the config
    if args is None:
        return cfg
    
    # Create parser
    parser = argparse.ArgumentParser(description='Simulation Runner')
    parser.add_argument('--icc', type=float, help='Single ICC value to simulate')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Random seed')
    parser.add_argument('--n-clusters', type=int, default=DEFAULT_N_CLUSTERS, help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=100, help='Observations per cluster')
    parser.add_argument('--icc-range', type=str, help='Comma-separated ICC values')
    parser.add_argument('--icc-step', type=float, help='Step size for ICC range')
    parser.add_argument('--alpha', type=float, help='Single alpha level (overrides alpha_levels)')
    parser.add_argument('--alpha-list', type=str, help='Comma-separated alpha levels')
    parser.add_argument('--n-permutations', type=int, default=1000, help='Number of permutations for block test')
    parser.add_argument('--output-baseline', type=str, help='Output path for baseline results')
    parser.add_argument('--output-robust', type=str, help='Output path for robust results')
    
    # Parse arguments
    parsed_args = parser.parse_args(args=args.__dict__.keys() if hasattr(args, '__dict__') else None)
    
    # Handle single ICC
    if hasattr(parsed_args, 'icc') and parsed_args.icc is not None:
        cfg['icc_range'] = [parsed_args.icc]
    
    # Handle ICC range override
    if hasattr(parsed_args, 'icc_range') and parsed_args.icc_range is not None:
        cfg['icc_range'] = [float(x) for x in parsed_args.icc_range.split(',')]
    
    # Handle ICC step
    if hasattr(parsed_args, 'icc_step') and parsed_args.icc_step is not None:
        cfg['icc_step'] = parsed_args.icc_step
    
    # Handle alpha level
    if hasattr(parsed_args, 'alpha') and parsed_args.alpha is not None:
        cfg['alpha_levels'] = [parsed_args.alpha]
    
    # Handle alpha list
    if hasattr(parsed_args, 'alpha_list') and parsed_args.alpha_list is not None:
        cfg['alpha_levels'] = [float(x) for x in parsed_args.alpha_list.split(',')]
    
    # Handle other parameters
    if hasattr(parsed_args, 'iterations') and parsed_args.iterations is not None:
        cfg['iterations'] = parsed_args.iterations
    if hasattr(parsed_args, 'seed') and parsed_args.seed is not None:
        cfg['seed'] = parsed_args.seed
    if hasattr(parsed_args, 'n_clusters') and parsed_args.n_clusters is not None:
        cfg['n_clusters'] = parsed_args.n_clusters
    if hasattr(parsed_args, 'n_obs_per_cluster') and parsed_args.n_obs_per_cluster is not None:
        cfg['n_obs_per_cluster'] = parsed_args.n_obs_per_cluster
    if hasattr(parsed_args, 'n_permutations') and parsed_args.n_permutations is not None:
        cfg['n_permutations'] = parsed_args.n_permutations
    if hasattr(parsed_args, 'output_baseline') and parsed_args.output_baseline is not None:
        cfg['output_baseline'] = parsed_args.output_baseline
    if hasattr(parsed_args, 'output_robust') and parsed_args.output_robust is not None:
        cfg['output_robust'] = parsed_args.output_robust
        
    return cfg
