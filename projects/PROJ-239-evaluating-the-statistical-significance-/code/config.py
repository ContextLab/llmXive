"""
Configuration module for the A/B test statistical significance simulation.

Defines default parameters, validation logic, and CLI argument parsing.
"""
import argparse
import numpy as np
from typing import Dict, Any, List, Optional

# Default simulation parameters
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42
DEFAULT_N_OBS_PER_CLUSTER = 10
MIN_CLUSTERS_FOR_ROBUST = 50

# Memory constraints (in GB)
MAX_MEMORY_GB = 7.0
MEMORY_WARNING_THRESHOLD_GB = 6.0


def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility.
    
    Args:
        seed: Integer seed value for numpy random generator.
    """
    np.random.seed(seed)


def load_config() -> Dict[str, Any]:
    """Load default configuration values.
    
    Returns:
        Dictionary containing all default configuration parameters.
    """
    return {
        'icc_range': ICC_RANGE.copy(),
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS.copy(),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': DEFAULT_N_OBS_PER_CLUSTER,
        'seed': DEFAULT_SEED,
        'max_memory_gb': MAX_MEMORY_GB,
        'memory_warning_threshold_gb': MEMORY_WARNING_THRESHOLD_GB,
        'min_clusters_for_robust': MIN_CLUSTERS_FOR_ROBUST
    }


def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate configuration parameters.
    
    Args:
        cfg: Configuration dictionary to validate.
        
    Raises:
        ValueError: If configuration parameters are invalid.
    """
    if cfg['n_clusters'] < MIN_CLUSTERS_FOR_ROBUST:
        # Only allow low cluster count if ICC is 0.0 (independent data)
        if cfg.get('icc', 0.0) != 0.0:
            raise ValueError(
                f"n_clusters ({cfg['n_clusters']}) must be at least "
                f"{MIN_CLUSTERS_FOR_ROBUST} for robust methods when ICC > 0.0"
            )
    
    if not isinstance(cfg['alpha_levels'], list) or len(cfg['alpha_levels']) == 0:
        raise ValueError("alpha_levels must be a non-empty list")
        
    if not isinstance(cfg['icc_range'], list) or len(cfg['icc_range']) == 0:
        raise ValueError("icc_range must be a non-empty list")
        
    if cfg['seed'] is not None and not isinstance(cfg['seed'], int):
        raise ValueError("seed must be an integer or None")


def parse_cli_args() -> Dict[str, Any]:
    """Parse command-line arguments and return configuration dictionary.
    
    Returns:
        Dictionary containing configuration with CLI overrides applied.
    """
    parser = argparse.ArgumentParser(
        description='A/B test simulation with cluster-robust inference'
    )
    
    parser.add_argument(
        '--icc-range',
        type=float,
        nargs='+',
        help='List of ICC values to test (e.g., --icc-range 0.0 0.1 0.2)'
    )
    
    parser.add_argument(
        '--icc-step',
        type=float,
        help='Step size for ICC range if not explicitly provided'
    )
    
    parser.add_argument(
        '--alpha-list',
        type=float,
        nargs='+',
        help='List of alpha levels for significance testing (e.g., --alpha-list 0.01 0.05 0.10)'
    )
    
    parser.add_argument(
        '--n-clusters',
        type=int,
        help='Number of clusters for simulation'
    )
    
    parser.add_argument(
        '--n-obs-per-cluster',
        type=int,
        help='Number of observations per cluster'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        help='Number of simulation iterations'
    )
    
    args = parser.parse_args()
    
    # Start with default config
    cfg = load_config()
    
    # Apply CLI overrides
    if args.icc_range is not None:
        cfg['icc_range'] = args.icc_range
    if args.icc_step is not None:
        cfg['icc_step'] = args.icc_step
    if args.alpha_list is not None:
        cfg['alpha_levels'] = args.alpha_list
    if args.n_clusters is not None:
        cfg['n_clusters'] = args.n_clusters
    if args.n_obs_per_cluster is not None:
        cfg['n_obs_per_cluster'] = args.n_obs_per_cluster
    if args.seed is not None:
        cfg['seed'] = args.seed
    if args.iterations is not None:
        cfg['iterations'] = args.iterations
        
    return cfg