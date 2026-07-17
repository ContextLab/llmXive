"""
Configuration module for the A/B test significance evaluation pipeline.

Defines simulation parameters, validation logic, and CLI argument parsing.
"""
import argparse
import numpy as np
from typing import Dict, Any, List, Optional
import os
import sys

# Constants defined in T004
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42
DEFAULT_N_OBS_PER_CLUSTER = 20

# Memory and time limits (FR-006, SC-003)
MEMORY_LIMIT_GB = 7.0
TIME_LIMIT_HOURS = 6

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    np.random.seed(seed)

def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary.
    
    Args:
        cfg: Configuration dictionary containing simulation parameters.
        
    Raises:
        ValueError: If configuration is invalid.
    """
    if 'icc' in cfg:
        if cfg['icc'] == 0.0:
            # Allow fewer clusters for independent data
            pass
        else:
            if cfg.get('n_clusters', DEFAULT_N_CLUSTERS) < 50:
                raise ValueError(f"n_clusters must be >= 50 for ICC > 0.0, got {cfg['n_clusters']}")
    
    if 'icc_range' in cfg:
        if not isinstance(cfg['icc_range'], list) or len(cfg['icc_range']) == 0:
            raise ValueError("icc_range must be a non-empty list")
        if any(not isinstance(x, (int, float)) for x in cfg['icc_range']):
            raise ValueError("All ICC values must be numeric")
    
    if 'alpha_levels' in cfg:
        if not isinstance(cfg['alpha_levels'], list) or len(cfg['alpha_levels']) == 0:
            raise ValueError("alpha_levels must be a non-empty list")
        if any(not (0 < x < 1) for x in cfg['alpha_levels']):
            raise ValueError("All alpha levels must be between 0 and 1")

def load_config(cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load configuration from defaults and optional CLI overrides.
    
    Args:
        cli_args: Dictionary of CLI arguments (from parse_cli_args).
                
    Returns:
        Configuration dictionary with all parameters.
    """
    cfg = {
        'icc_range': ICC_RANGE,
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS,
        'n_clusters': DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': DEFAULT_N_OBS_PER_CLUSTER,
        'seed': DEFAULT_SEED,
        'n_permutations': 1000,
        'output_baseline': 'data/derived/baseline_results.csv',
        'output_robust': 'data/derived/robustResults.csv',
        'mode': 'full',  # 'baseline', 'robust', or 'full'
    }
    
    if cli_args:
        # Override with CLI values if present
        if 'icc' in cli_args and cli_args['icc'] is not None:
            cfg['icc'] = cli_args['icc']
        if 'icc_range' in cli_args and cli_args['icc_range'] is not None:
            cfg['icc_range'] = cli_args['icc_range']
        if 'icc_step' in cli_args and cli_args['icc_step'] is not None:
            cfg['icc_step'] = cli_args['icc_step']
        if 'alpha' in cli_args and cli_args['alpha'] is not None:
            cfg['alpha_levels'] = [cli_args['alpha']]
        if 'alpha_list' in cli_args and cli_args['alpha_list'] is not None:
            # Parse comma-separated alpha levels
            alpha_str = cli_args['alpha_list']
            cfg['alpha_levels'] = [float(x.strip()) for x in alpha_str.split(',')]
        if 'n_clusters' in cli_args and cli_args['n_clusters'] is not None:
            cfg['n_clusters'] = cli_args['n_clusters']
        if 'n_obs_per_cluster' in cli_args and cli_args['n_obs_per_cluster'] is not None:
            cfg['n_obs_per_cluster'] = cli_args['n_obs_per_cluster']
        if 'seed' in cli_args and cli_args['seed'] is not None:
            cfg['seed'] = cli_args['seed']
        if 'n_permutations' in cli_args and cli_args['n_permutations'] is not None:
            cfg['n_permutations'] = cli_args['n_permutations']
        if 'output_baseline' in cli_args and cli_args['output_baseline'] is not None:
            cfg['output_baseline'] = cli_args['output_baseline']
        if 'output_robust' in cli_args and cli_args['output_robust'] is not None:
            cfg['output_robust'] = cli_args['output_robust']
        if 'mode' in cli_args and cli_args['mode'] is not None:
            cfg['mode'] = cli_args['mode']
        
        # Handle iterations if passed (used by simulation_runner)
        if 'iterations' in cli_args and cli_args['iterations'] is not None:
            cfg['iterations'] = cli_args['iterations']
    
    validate_config(cfg)
    return cfg

def parse_cli_args(args: Optional[List[str]] = None, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parse command-line arguments and return a config dictionary.
    
    This function supports multiple calling patterns:
    1. parse_cli_args() - Returns config with defaults
    2. parse_cli_args(args) - Parses args and returns new config
    3. parse_cli_args(args, cfg) - Parses args and updates existing config
    
    Args:
        args: List of command-line arguments (defaults to sys.argv[1:])
        cfg: Optional existing config dictionary to update
                
    Returns:
        Configuration dictionary with CLI overrides applied.
    """
    parser = argparse.ArgumentParser(
        description='A/B test significance evaluation with cluster-robust methods'
    )
    
    # Simulation parameters
    parser.add_argument('--icc', type=float, default=None,
                      help='Single ICC value to simulate (overrides icc_range)')
    parser.add_argument('--icc-range', type=float, nargs='+', default=None,
                      help='List of ICC values to simulate')
    parser.add_argument('--icc-step', type=float, default=None,
                      help='Step size for ICC range generation')
    parser.add_argument('--n-clusters', type=int, default=None,
                      help='Number of clusters')
    parser.add_argument('--n-obs-per-cluster', type=int, default=None,
                      help='Number of observations per cluster')
    parser.add_argument('--iterations', type=int, default=None,
                      help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, default=None,
                      help='Random seed for reproducibility')
    
    # Alpha levels (FR-005)
    parser.add_argument('--alpha', type=float, default=None,
                      help='Single alpha level for significance testing')
    parser.add_argument('--alpha-list', type=str, default=None,
                      help='Comma-separated list of alpha levels (e.g., "0.01,0.05,0.10")')
    
    # Robust method parameters
    parser.add_argument('--n-permutations', type=int, default=None,
                      help='Number of permutations for block permutation test')
    
    # Output paths
    parser.add_argument('--output-baseline', type=str, default=None,
                      help='Output path for baseline results CSV')
    parser.add_argument('--output-robust', type=str, default=None,
                      help='Output path for robust results CSV')
    
    # Mode selection
    parser.add_argument('--mode', type=str, choices=['baseline', 'robust', 'full'],
                      default=None, help='Simulation mode: baseline, robust, or full')
    
    parsed_args = parser.parse_args(args)
    
    # Convert parsed args to dictionary
    cli_dict = vars(parsed_args)
    
    if cfg is not None:
        # Update existing config
        cfg.update(cli_dict)
        return cfg
    else:
        # Return new config with CLI overrides
        return load_config(cli_dict)