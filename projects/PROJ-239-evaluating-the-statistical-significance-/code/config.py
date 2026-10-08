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

# Minimum number of alpha levels required by SC-004
MIN_ALPHA_LEVELS = 3

def validate_config(cfg: Dict[str, Any]) -> None:
    """Validate simulation configuration parameters.

    Args:
        cfg: Configuration dictionary.

    Raises:
        ValueError: If n_clusters < 50.
    """
    if cfg.get('n_clusters', DEFAULT_N_CLUSTERS) < 50:
        raise ValueError(f"n_clusters must be >= 50, got {cfg['n_clusters']}")

def validate_alpha_levels(alphas: List[float]) -> None:
    """Validate that the alpha levels list meets minimum requirements.

    Per SC-004, at least 3 alpha levels must be provided to ensure
    robust statistical evaluation.

    Args:
        alphas: List of significance levels (floats).

    Raises:
        ValueError: If len(alphas) < 3.
    """
    if not isinstance(alphas, list) or len(alphas) < MIN_ALPHA_LEVELS:
        raise ValueError(
            f"SC-004 Compliance: At least {MIN_ALPHA_LEVELS} alpha levels "
            f"are required. Got {len(alphas)}."
        )

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility.

    Args:
        seed: Integer seed value.
    """
    np.random.seed(seed)

def load_config(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """Load configuration from defaults and optional CLI overrides.

    This function handles the full lifecycle:
    1. Start with defaults.
    2. Parse CLI arguments if provided.
    3. Validate constraints (including alpha count).
    4. Return the final config.

    Args:
        cli_args: Optional list of CLI arguments (sys.argv[1:] if None).

    Returns:
        Complete configuration dictionary.

    Raises:
        ValueError: If validation fails (e.g., alpha count < 3).
    """
    cfg = {
        'icc_range': list(ICC_RANGE),
        'icc_step': ICC_STEP,
        'alpha_levels': list(ALPHA_LEVELS),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'cluster_mean': CLUSTER_MEAN_SIZE,
        'cluster_std': CLUSTER_STD_SIZE,
        'seed': DEFAULT_SEED,
        'iterations': DEFAULT_ITERATIONS,
        'n_obs_per_cluster': None, # Calculated later or set via CLI
        'n_permutations': 1000,
        'output': None,
        'verbose': False
    }

    if cli_args is None:
        cli_args = sys.argv[1:]

    if cli_args:
        cfg = parse_cli_args(cli_args, cfg)

    # Validate alpha levels (SC-004)
    validate_alpha_levels(cfg['alpha_levels'])

    # Validate n_clusters
    validate_config(cfg)

    return cfg

def parse_cli_args(args: Union[List[str], argparse.Namespace], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse CLI arguments and update configuration.

    Supports multiple call patterns for flexibility:
    1. parse_cli_args() -> Returns config with defaults (not supported directly, use load_config)
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)

    Args:
        args: Either a list of CLI strings, an argparse.Namespace, or a config dict.
        cfg: Optional existing config dict to update.

    Returns:
        Updated configuration dictionary.

    Raises:
        ValueError: If alpha levels validation fails.
    """
    # Pattern 4: args is actually a config dict, no CLI provided
    if isinstance(args, dict):
        if cfg is None:
            cfg = args
        else:
            # Merge args into cfg
            cfg.update(args)
        return cfg

    # If cfg is None, start with defaults
    if cfg is None:
        cfg = {
            'icc_range': list(ICC_RANGE),
            'icc_step': ICC_STEP,
            'alpha_levels': list(ALPHA_LEVELS),
            'n_clusters': DEFAULT_N_CLUSTERS,
            'cluster_mean': CLUSTER_MEAN_SIZE,
            'cluster_std': CLUSTER_STD_SIZE,
            'seed': DEFAULT_SEED,
            'iterations': DEFAULT_ITERATIONS,
            'n_obs_per_cluster': None,
            'n_permutations': 1000,
            'output': None,
            'verbose': False
        }

    # If args is a Namespace, convert to list
    if isinstance(args, argparse.Namespace):
        args = vars(args)

    # If args is a list, parse it
    if isinstance(args, list):
        parser = argparse.ArgumentParser(
            description='Simulation configuration CLI',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        # ICC Configuration
        parser.add_argument('--icc-range', type=str, default=None,
                            help='Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)')
        parser.add_argument('--icc-step', type=float, default=None,
                            help='Step size for ICC range')

        # Alpha Configuration (T023, T022b)
        parser.add_argument('--alpha-list', type=str, default=None,
                            help='Comma-separated list of alpha levels (e.g., 0.01,0.05,0.10). '
                                 f'Must contain at least {MIN_ALPHA_LEVELS} values.')
        parser.add_argument('--alpha', type=float, default=None,
                            help='Single alpha level (deprecated, use --alpha-list). '
                                 'If provided, overrides alpha-list if only 1 value.')

        # Cluster Configuration (T040)
        parser.add_argument('--cluster-mean', type=float, default=None,
                            help='Mean cluster size')
        parser.add_argument('--cluster-std', type=float, default=None,
                            help='Std dev of cluster size')
        parser.add_argument('--n-clusters', type=int, default=None,
                            help='Number of clusters')
        parser.add_argument('--n-obs-per-cluster', type=int, default=None,
                            help='Observations per cluster')

        # Simulation Control
        parser.add_argument('--seed', type=int, default=None,
                            help='Random seed')
        parser.add_argument('--iterations', type=int, default=None,
                            help='Number of simulation iterations')
        parser.add_argument('--n-permutations', type=int, default=None,
                            help='Number of permutations for block test')

        # Output
        parser.add_argument('--output', type=str, default=None,
                            help='Output file path')
        parser.add_argument('--verbose', action='store_true',
                            help='Enable verbose logging')

        parsed = parser.parse_args(args)
        parsed_dict = vars(parsed)
    else:
        # Assume args is already a dict (e.g., from vars(namespace))
        parsed_dict = args

    # Apply overrides
    if parsed_dict.get('icc_range') is not None:
        cfg['icc_range'] = [float(x) for x in parsed_dict['icc_range'].split(',')]

    if parsed_dict.get('icc_step') is not None:
        cfg['icc_step'] = parsed_dict['icc_step']

    # Handle Alpha Levels
    if parsed_dict.get('alpha_list') is not None:
        alphas = [float(x) for x in parsed_dict['alpha_list'].split(',')]
        cfg['alpha_levels'] = alphas
    elif parsed_dict.get('alpha') is not None:
        # If single alpha provided, convert to list but warn if < 3
        cfg['alpha_levels'] = [parsed_dict['alpha']]

    if parsed_dict.get('cluster_mean') is not None:
        cfg['cluster_mean'] = parsed_dict['cluster_mean']

    if parsed_dict.get('cluster_std') is not None:
        cfg['cluster_std'] = parsed_dict['cluster_std']

    if parsed_dict.get('n_clusters') is not None:
        cfg['n_clusters'] = parsed_dict['n_clusters']

    if parsed_dict.get('n_obs_per_cluster') is not None:
        cfg['n_obs_per_cluster'] = parsed_dict['n_obs_per_cluster']

    if parsed_dict.get('seed') is not None:
        cfg['seed'] = parsed_dict['seed']

    if parsed_dict.get('iterations') is not None:
        cfg['iterations'] = parsed_dict['iterations']

    if parsed_dict.get('n_permutations') is not None:
        cfg['n_permutations'] = parsed_dict['n_permutations']

    if parsed_dict.get('output') is not None:
        cfg['output'] = parsed_dict['output']

    if parsed_dict.get('verbose'):
        cfg['verbose'] = parsed_dict['verbose']

    # Final validation of alpha levels
    validate_alpha_levels(cfg['alpha_levels'])

    return cfg