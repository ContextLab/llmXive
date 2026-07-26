"""
Configuration management for the A/B test significance simulation.

This module defines simulation parameters, validation logic, and CLI parsing
to support user-configurable ICC ranges and alpha levels.
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

# Default cluster generation parameters (from T010)
AVG_CLUSTER_SIZE = 12.5
STD_CLUSTER_SIZE = 8.2


def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    np.random.seed(seed)


def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary.

    Args:
        cfg: Configuration dictionary containing 'icc', 'n_clusters', etc.

    Raises:
        ValueError: If configuration values are invalid.
    """
    # Validate ICC
    icc = cfg.get('icc')
    if icc is not None:
        if not isinstance(icc, (int, float)):
            raise ValueError(f"icc must be a number, got {type(icc)}")
        if icc < 0.0 or icc > 1.0:
            raise ValueError(f"icc must be between 0.0 and 1.0, got {icc}")

    # Validate n_clusters
    n_clusters = cfg.get('n_clusters')
    if n_clusters is not None:
        if not isinstance(n_clusters, int):
            raise ValueError(f"n_clusters must be an integer, got {type(n_clusters)}")
        # Only enforce minimum if icc != 0.0
        if icc != 0.0 and n_clusters < 50:
            raise ValueError(f"n_clusters must be >= 50 for robust methods (icc={icc}), got {n_clusters}")

    # Validate alpha_levels
    alpha_levels = cfg.get('alpha_levels')
    if alpha_levels is not None:
        if not isinstance(alpha_levels, list) or len(alpha_levels) == 0:
            raise ValueError("alpha_levels must be a non-empty list")
        for alpha in alpha_levels:
            if not isinstance(alpha, (int, float)) or alpha <= 0 or alpha >= 1:
                raise ValueError(f"alpha_level must be between 0 and 1, got {alpha}")

    # Validate icc_range
    icc_range = cfg.get('icc_range')
    if icc_range is not None:
        if not isinstance(icc_range, list) or len(icc_range) == 0:
            raise ValueError("icc_range must be a non-empty list")
        for val in icc_range:
            if not isinstance(val, (int, float)) or val < 0 or val > 1:
                raise ValueError(f"icc_range values must be between 0 and 1, got {val}")

    # Validate icc_step
    icc_step = cfg.get('icc_step')
    if icc_step is not None:
        if not isinstance(icc_step, (int, float)) or icc_step <= 0:
            raise ValueError(f"icc_step must be a positive number, got {icc_step}")


def load_config(cli_args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Load configuration with defaults, optionally overridden by CLI arguments.

    Args:
        cli_args: Parsed command-line arguments (optional).

    Returns:
        Configuration dictionary.
    """
    cfg = {
        'icc_range': list(ICC_RANGE),
        'icc_step': ICC_STEP,
        'alpha_levels': list(ALPHA_LEVELS),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'seed': DEFAULT_SEED,
        'icc': None,  # Will be set by CLI or iteration loop
        'n_iterations': 100,  # Default, can be overridden
        'n_obs_per_cluster': 12,  # Default, can be overridden
    }

    if cli_args:
        # Override alpha levels if provided
        if hasattr(cli_args, 'alpha_list') and cli_args.alpha_list:
            cfg['alpha_levels'] = [float(x) for x in cli_args.alpha_list.split(',')]

        # Override ICC range if provided
        if hasattr(cli_args, 'icc_range') and cli_args.icc_range:
            cfg['icc_range'] = [float(x) for x in cli_args.icc_range.split(',')]

        # Override ICC step if provided
        if hasattr(cli_args, 'icc_step') and cli_args.icc_step is not None:
            cfg['icc_step'] = float(cli_args.icc_step)

        # Override seed if provided
        if hasattr(cli_args, 'seed') and cli_args.seed is not None:
            cfg['seed'] = int(cli_args.seed)

        # Override n_iterations if provided
        if hasattr(cli_args, 'iterations') and cli_args.iterations is not None:
            cfg['n_iterations'] = int(cli_args.iterations)

        # Override n_clusters if provided
        if hasattr(cli_args, 'n_clusters') and cli_args.n_clusters is not None:
            cfg['n_clusters'] = int(cli_args.n_clusters)

        # Override n_obs_per_cluster if provided
        if hasattr(cli_args, 'n_obs_per_cluster') and cli_args.n_obs_per_cluster is not None:
            cfg['n_obs_per_cluster'] = int(cli_args.n_obs_per_cluster)

        # Override single ICC if provided (for single-run scripts)
        if hasattr(cli_args, 'icc') and cli_args.icc is not None:
            cfg['icc'] = float(cli_args.icc)

    return cfg


def parse_cli_args(
    args: Optional[Union[argparse.Namespace, List[str]]] = None,
    cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse command-line arguments and update configuration.

    This function supports multiple calling patterns for flexibility:
    1. parse_cli_args() -> Returns config with defaults
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)

    Args:
        args: Either a Namespace from argparse, a list of strings, or None.
             If a list is provided, it will be parsed as CLI arguments.
        cfg: Optional existing configuration dictionary to update.

    Returns:
        Updated configuration dictionary.
    """
    # Pattern 1: No arguments -> return default config
    if args is None and cfg is None:
        return load_config(None)

    # Pattern 4: Only cfg provided -> update with defaults, no CLI parsing
    if args is None and cfg is not None:
        default_cfg = load_config(None)
        default_cfg.update(cfg)
        validate_config(default_cfg)
        return default_cfg

    # Normalize args to argparse.Namespace if a list is provided
    if isinstance(args, list):
        parser = _create_arg_parser()
        args = parser.parse_args(args)

    # If we get here, args is a Namespace
    # Pattern 2 & 3: args provided, optionally with cfg
    if cfg is None:
        # Pattern 2: Create new config from CLI args
        cfg = load_config(args)
    else:
        # Pattern 3: Update existing config with CLI args
        cfg = load_config(args)
        # Preserve any keys from the original cfg that aren't in the new one
        # (though load_config already handles most overrides)
        for key, value in cfg.items():
            if key in cfg:
                cfg[key] = value

    validate_config(cfg)
    return cfg


def _create_arg_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all supported flags."""
    parser = argparse.ArgumentParser(
        description='A/B Test Significance Simulation Configuration',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # ICC configuration
    parser.add_argument(
        '--icc-range',
        type=str,
        default=None,
        help='Comma-separated ICC values (e.g., 0.0,0.1,0.2)'
    )
    parser.add_argument(
        '--icc-step',
        type=float,
        default=None,
        help='Step size for ICC values'
    )
    parser.add_argument(
        '--icc',
        type=float,
        default=None,
        help='Single ICC value for single-run simulations'
    )

    # Alpha configuration
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=None,
        help='Comma-separated alpha levels (e.g., 0.01,0.05,0.10)'
    )

    # Simulation parameters
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=None,
        help='Number of simulation iterations'
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

    return parser