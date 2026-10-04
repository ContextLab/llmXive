"""Configuration module for simulation parameters and validation."""
import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Union
import os
import sys

# Constants defined in T004
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
CLUSTER_MEAN_SIZE = 12.5
CLUSTER_STD_SIZE = 8.2
DEFAULT_SEED = 42
DEFAULT_ITERATIONS = 1000

def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate configuration parameters.
    
    Args:
        cfg: Configuration dictionary.
        
    Raises:
        ValueError: If n_clusters < 50.
    """
    if cfg.get('n_clusters', DEFAULT_N_CLUSTERS) < 50:
        raise ValueError(f"n_clusters must be >= 50, got {cfg['n_clusters']}")

def validate_alpha_levels(alphas: List[float]) -> None:
    """Validate alpha levels meet SC-004 requirement.
    
    Args:
        alphas: List of alpha levels.
        
    Raises:
        ValueError: If len(alphas) < 3.
    """
    if len(alphas) < 3:
        raise ValueError(f"SC-004 requires at least 3 alpha levels, got {len(alphas)}: {alphas}")

def load_config(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """Load configuration with optional CLI overrides.
    
    Args:
        cli_args: Optional list of CLI arguments. If None, uses sys.argv[1:].
        
    Returns:
        Configuration dictionary.
    """
    cfg = {
        'icc_range': ICC_RANGE.copy(),
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS.copy(),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'cluster_mean': CLUSTER_MEAN_SIZE,
        'cluster_std': CLUSTER_STD_SIZE,
        'seed': DEFAULT_SEED,
        'n_iterations': DEFAULT_ITERATIONS,
    }
    
    # If no args provided, return defaults
    if cli_args is None:
        if len(sys.argv) > 1:
            cli_args = sys.argv[1:]
        else:
            return cfg
    
    # Parse CLI args
    cfg = parse_cli_args(cli_args, cfg)
    return cfg

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility.
    
    Args:
        seed: Random seed.
    """
    np.random.seed(seed)

def parse_cli_args(cli_args: List[str], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse CLI arguments and update configuration.
    
    This function supports multiple call patterns to be tolerant of different
    usage scenarios across the codebase:
    1. parse_cli_args() -> Returns config with defaults (not supported directly, use load_config)
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)
    
    Args:
        cli_args: List of CLI arguments or a config dict (for pattern 4).
        cfg: Optional existing config to update.
        
    Returns:
        Updated configuration dictionary.
    """
    # Handle pattern 4: parse_cli_args(cfg) -> no CLI args, just defaults
    if isinstance(cli_args, dict) and cfg is None:
        cfg = cli_args.copy()
        return cfg
    
    # Handle pattern 2: parse_cli_args(args) -> no cfg provided
    if cfg is None:
        cfg = {
            'icc_range': ICC_RANGE.copy(),
            'icc_step': ICC_STEP,
            'alpha_levels': ALPHA_LEVELS.copy(),
            'n_clusters': DEFAULT_N_CLUSTERS,
            'cluster_mean': CLUSTER_MEAN_SIZE,
            'cluster_std': CLUSTER_STD_SIZE,
            'seed': DEFAULT_SEED,
            'n_iterations': DEFAULT_ITERATIONS,
        }
    
    # Ensure cli_args is a list
    if not isinstance(cli_args, list):
        cli_args = list(cli_args) if hasattr(cli_args, '__iter__') else []
    
    parser = argparse.ArgumentParser(description='Simulation configuration')
    
    # ICC parameters
    parser.add_argument('--icc-range', type=str, default=None,
                      help='Comma-separated ICC values, e.g., 0.0,0.1,0.2')
    parser.add_argument('--icc-step', type=float, default=None,
                      help='Step size for ICC range')
    
    # Alpha levels
    parser.add_argument('--alpha-list', type=str, default=None,
                      help='Comma-separated alpha levels, e.g., 0.01,0.05,0.10')
    
    # Cluster size parameters
    parser.add_argument('--cluster-mean', type=float, default=None,
                      help='Mean cluster size')
    parser.add_argument('--cluster-std', type=float, default=None,
                      help='Standard deviation of cluster size')
    
    # Simulation parameters
    parser.add_argument('--seed', type=int, default=None,
                      help='Random seed')
    parser.add_argument('--iterations', type=int, default=None,
                      help='Number of iterations')
    
    args = parser.parse_args(cli_args)
    
    # Apply overrides
    if args.icc_range is not None:
        cfg['icc_range'] = [float(x) for x in args.icc_range.split(',')]
    
    if args.icc_step is not None:
        cfg['icc_step'] = args.icc_step
    
    if args.alpha_list is not None:
        cfg['alpha_levels'] = [float(x) for x in args.alpha_list.split(',')]
        # Validate alpha levels per SC-004
        validate_alpha_levels(cfg['alpha_levels'])
    
    if args.cluster_mean is not None:
        cfg['cluster_mean'] = args.cluster_mean
    
    if args.cluster_std is not None:
        cfg['cluster_std'] = args.cluster_std
    
    if args.seed is not None:
        cfg['seed'] = args.seed
    
    if args.iterations is not None:
        cfg['n_iterations'] = args.iterations
    
    return cfg