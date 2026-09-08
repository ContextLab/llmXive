"""
Configuration management for the A/B test simulation pipeline.
Handles CLI argument parsing, validation, and default settings.
"""
import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Union
import os
import sys

# Constants from T004
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42
DEFAULT_N_OBS_PER_CLUSTER = 12

# Memory constraints (from T027)
MEMORY_LIMIT_GB = 7.0
MIN_CLUSTERS_FOR_ROBUST = 50

def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validates the configuration dictionary.
    Raises ValueError if constraints are violated.
    """
    if 'icc' in cfg:
        icc = cfg['icc']
        if icc is None:
            raise ValueError("ICC cannot be None.")
        if not isinstance(icc, (int, float)):
            raise ValueError(f"ICC must be a number, got {type(icc)}")
        if icc < 0.0 or icc > 1.0:
            raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")

    if 'n_clusters' in cfg:
        n_clusters = cfg['n_clusters']
        if n_clusters is None:
            raise ValueError("n_clusters cannot be None.")
        if not isinstance(n_clusters, int) or n_clusters < 1:
            raise ValueError(f"n_clusters must be a positive integer, got {n_clusters}")
        
        # T004 logic: if icc is 0.0, we can have fewer clusters (independent data)
        # But for robust methods (which this validator might be used for), we enforce min
        icc = cfg.get('icc', 0.0)
        if icc != 0.0 and n_clusters < MIN_CLUSTERS_FOR_ROBUST:
            raise ValueError(f"n_clusters must be at least {MIN_CLUSTERS_FOR_ROBUST} for ICC > 0.0 to ensure robust variance validity.")

    if 'alpha_levels' in cfg:
        alphas = cfg['alpha_levels']
        if not alphas or not all(isinstance(a, (int, float)) and 0 < a < 1 for a in alphas):
            raise ValueError("alpha_levels must be a non-empty list of floats between 0 and 1.")

def load_config(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Loads configuration from defaults and optionally CLI arguments.
    Returns a dictionary of configuration parameters.
    """
    cfg = {
        'icc_range': list(ICC_RANGE),
        'icc_step': ICC_STEP,
        'alpha_levels': list(ALPHA_LEVELS),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': DEFAULT_N_OBS_PER_CLUSTER,
        'seed': DEFAULT_SEED,
        'icc': None,  # Specific ICC if running single point
        'n_iterations': 100,  # Default iterations
        'method': 'baseline',  # 'baseline' or 'robust'
    }
    
    if cli_args is not None:
        cfg = parse_cli_args(cli_args, cfg)
    
    # If specific ICC is set, override range to just that value for single-point runs
    if cfg.get('icc') is not None:
        cfg['icc_range'] = [cfg['icc']]
        
    return cfg

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    np.random.seed(seed)

def parse_cli_args(args: Optional[Union[List[str], argparse.Namespace]] = None, 
                   cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses command-line arguments and updates the configuration.
    
    Supports multiple call signatures for flexibility:
    1. parse_cli_args() -> Returns config with defaults
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)
    """
    # Handle call signature 4: parse_cli_args(cfg)
    if args is None and cfg is not None:
        # No CLI args, just return a copy of the provided config
        return cfg.copy() if cfg else load_config()
    
    # Handle call signature 1: parse_cli_args()
    if args is None and cfg is None:
        return load_config()
    
    # If args is a Namespace, convert to list
    if isinstance(args, argparse.Namespace):
        # We need to reconstruct args from namespace or use namespace directly
        # For simplicity, if it's a namespace, we treat it as the source
        # But standard argparse returns Namespace, so we need to extract values
        # Let's assume if it's a Namespace, we use its attributes directly
        parsed = args
    else:
        # It's a list or None (handled above)
        parser = argparse.ArgumentParser(
            description="A/B Test Simulation Configuration",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument(
            '--icc-range',
            type=str,
            default=None,
            help='Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)'
        )
        parser.add_argument(
            '--icc-step',
            type=float,
            default=None,
            help='Step size for ICC range'
        )
        parser.add_argument(
            '--alpha-list',
            type=str,
            default=None,
            help='Comma-separated list of alpha levels (e.g., 0.01,0.05,0.10)'
        )
        parser.add_argument(
            '--icc',
            type=float,
            default=None,
            help='Single ICC value for point simulation'
        )
        parser.add_argument(
            '--n-clusters',
            type=int,
            default=None,
            help='Number of clusters'
        )
        parser.add_argument(
            '--n-obs-per-cluster',
            type=int,
            default=None,
            help='Average number of observations per cluster'
        )
        parser.add_argument(
            '--n-iterations',
            type=int,
            default=None,
            help='Number of simulation iterations'
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=None,
            help='Random seed'
        )
        parser.add_argument(
            '--method',
            type=str,
            default=None,
            choices=['baseline', 'robust', 'full'],
            help='Simulation method'
        )
        
        # Parse arguments
        if args is None:
            parsed = parser.parse_args()
        else:
            parsed = parser.parse_args(args)
    
    # If no base config provided, start with defaults
    if cfg is None:
        cfg = load_config()
    
    # Update config from parsed arguments
    if parsed.icc_range:
        cfg['icc_range'] = [float(x) for x in parsed.icc_range.split(',')]
    
    if parsed.icc_step is not None:
        cfg['icc_step'] = parsed.icc_step
    
    if parsed.alpha_list:
        cfg['alpha_levels'] = [float(x) for x in parsed.alpha_list.split(',')]
    
    if parsed.icc is not None:
        cfg['icc'] = parsed.icc
    
    if parsed.n_clusters is not None:
        cfg['n_clusters'] = parsed.n_clusters
    
    if parsed.n_obs_per_cluster is not None:
        cfg['n_obs_per_cluster'] = parsed.n_obs_per_cluster
    
    if parsed.n_iterations is not None:
        cfg['n_iterations'] = parsed.n_iterations
    
    if parsed.seed is not None:
        cfg['seed'] = parsed.seed
    
    if parsed.method is not None:
        cfg['method'] = parsed.method
    
    # Validate the final config
    validate_config(cfg)
    
    return cfg
