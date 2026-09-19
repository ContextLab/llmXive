import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Union
import os
import sys

# Constants
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42

def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validates the configuration dictionary.
    
    Raises:
        ValueError: If configuration is invalid.
    """
    icc = cfg.get('icc')
    n_clusters = cfg.get('n_clusters')
    
    if icc is not None:
        if icc < 0.0 or icc > 1.0:
            raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")
    
    if n_clusters is not None:
        if n_clusters < 50 and icc != 0.0:
            raise ValueError(f"n_clusters must be >= 50 for ICC > 0.0, got {n_clusters}")

def load_config(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Loads configuration, optionally parsing CLI arguments.
    
    Args:
        cli_args: Optional list of CLI arguments. If None, uses sys.argv.
                
    Returns:
        A dictionary containing the configuration.
    """
    cfg = {
        'icc': None,
        'icc_range': ICC_RANGE,
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS,
        'n_clusters': DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': 10,
        'seed': DEFAULT_SEED,
        'iterations': 100,
        'method': 'baseline'
    }
    
    if cli_args is None and len(sys.argv) > 1:
        cli_args = sys.argv[1:]
        
    if cli_args:
        cfg = parse_cli_args(cli_args, cfg)
        
    return cfg

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    np.random.seed(seed)

def parse_cli_args(args: Union[List[str], argparse.Namespace, None], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Parses command-line arguments and updates the configuration.
    
    This function is designed to be flexible and accept various input shapes:
    1. parse_cli_args() -> Returns config with defaults
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)
    
    Args:
        args: Can be a list of strings, an argparse.Namespace, or None.
        cfg: An existing configuration dictionary to update, or None to create a new one.
                
    Returns:
        A dictionary containing the updated configuration.
                
    Raises:
        ValueError: If configuration is invalid after parsing.
    """
    # Handle case 1: No args, no cfg -> return default config
    if args is None and cfg is None:
        cfg = {
            'icc': None,
            'icc_range': ICC_RANGE,
            'icc_step': ICC_STEP,
            'alpha_levels': ALPHA_LEVELS,
            'n_clusters': DEFAULT_N_CLUSTERS,
            'n_obs_per_cluster': 10,
            'seed': DEFAULT_SEED,
            'iterations': 100,
            'method': 'baseline'
        }
        validate_config(cfg)
        return cfg
        
    # Handle case 4: args is a dict (cfg), no CLI args -> just validate and return
    if isinstance(args, dict) and cfg is None:
        cfg = args
        validate_config(cfg)
        return cfg
        
    # Handle case 2: args is a list/namespace, no cfg -> create new config and parse
    if cfg is None:
        cfg = {
            'icc': None,
            'icc_range': ICC_RANGE,
            'icc_step': ICC_STEP,
            'alpha_levels': ALPHA_LEVELS,
            'n_clusters': DEFAULT_N_CLUSTERS,
            'n_obs_per_cluster': 10,
            'seed': DEFAULT_SEED,
            'iterations': 100,
            'method': 'baseline'
        }
        
    # If args is an argparse.Namespace, convert to list
    if isinstance(args, argparse.Namespace):
        args = vars(args)
        
    # If args is a dict (parsed namespace), handle directly
    if isinstance(args, dict):
        if 'icc' in args and args['icc'] is not None:
            cfg['icc'] = float(args['icc'])
        if 'icc_range' in args and args['icc_range'] is not None:
            cfg['icc_range'] = [float(x) for x in args['icc_range'].split(',')]
        if 'icc_step' in args and args['icc_step'] is not None:
            cfg['icc_step'] = float(args['icc_step'])
        if 'alpha_list' in args and args['alpha_list'] is not None:
            cfg['alpha_levels'] = [float(x) for x in args['alpha_list'].split(',')]
        if 'n_clusters' in args and args['n_clusters'] is not None:
            cfg['n_clusters'] = int(args['n_clusters'])
        if 'n_obs_per_cluster' in args and args['n_obs_per_cluster'] is not None:
            cfg['n_obs_per_cluster'] = int(args['n_obs_per_cluster'])
        if 'seed' in args and args['seed'] is not None:
            cfg['seed'] = int(args['seed'])
        if 'iterations' in args and args['iterations'] is not None:
            cfg['iterations'] = int(args['iterations'])
        if 'method' in args and args['method'] is not None:
            cfg['method'] = args['method']
            
    # If args is a list, parse with argparse
    elif isinstance(args, list):
        parser = argparse.ArgumentParser(description='Simulation Configuration')
        parser.add_argument('--icc', type=float, help='Intra-cluster correlation coefficient')
        parser.add_argument('--icc-range', type=str, help='Comma-separated ICC values')
        parser.add_argument('--icc-step', type=float, help='Step size for ICC range')
        parser.add_argument('--alpha-list', type=str, help='Comma-separated alpha levels')
        parser.add_argument('--n-clusters', type=int, help='Number of clusters')
        parser.add_argument('--n-obs-per-cluster', type=int, help='Number of observations per cluster')
        parser.add_argument('--seed', type=int, help='Random seed')
        parser.add_argument('--iterations', type=int, help='Number of iterations')
        parser.add_argument('--method', type=str, choices=['baseline', 'robust', 'full'], help='Simulation method')
        
        parsed_args = parser.parse_args(args)
        
        if parsed_args.icc is not None:
            cfg['icc'] = float(parsed_args.icc)
        if parsed_args.icc_range is not None:
            cfg['icc_range'] = [float(x) for x in parsed_args.icc_range.split(',')]
        if parsed_args.icc_step is not None:
            cfg['icc_step'] = float(parsed_args.icc_step)
        if parsed_args.alpha_list is not None:
            cfg['alpha_levels'] = [float(x) for x in parsed_args.alpha_list.split(',')]
        if parsed_args.n_clusters is not None:
            cfg['n_clusters'] = int(parsed_args.n_clusters)
        if parsed_args.n_obs_per_cluster is not None:
            cfg['n_obs_per_cluster'] = int(parsed_args.n_obs_per_cluster)
        if parsed_args.seed is not None:
            cfg['seed'] = int(parsed_args.seed)
        if parsed_args.iterations is not None:
            cfg['iterations'] = int(parsed_args.iterations)
        if parsed_args.method is not None:
            cfg['method'] = parsed_args.method
            
    validate_config(cfg)
    return cfg
