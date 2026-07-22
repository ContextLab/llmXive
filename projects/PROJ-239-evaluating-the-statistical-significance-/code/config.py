"""
Configuration management for the A/B test simulation pipeline.
Handles simulation parameters, validation, and CLI argument parsing.
"""

import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Union
import os
import sys

# Default constants
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42
DEFAULT_N_OBS_PER_CLUSTER = 20

# CLI argument names for robust parsing
CLI_ICC_RANGE = 'icc_range'
CLI_ICC_STEP = 'icc_step'
CLI_ALPHA_LIST = 'alpha_list'
CLI_N_CLUSTERS = 'n_clusters'
CLI_N_OBS_PER_CLUSTER = 'n_obs_per_cluster'
CLI_SEED = 'seed'
CLI_ICC = 'icc'
CLI_ITERATIONS = 'iterations'
CLI_ALPHA = 'alpha'
CLI_N_PERMUTATIONS = 'n_permutations'
CLI_OUTPUT_BASELINE = 'output_baseline'
CLI_OUTPUT_ROBUST = 'output_robust'
CLI_MODE = 'mode'


def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    np.random.seed(seed)


def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary.

    Raises ValueError if:
    - n_clusters < 50 unless icc == 0.0
    - icc is outside [0.0, 1.0]
    - alpha is not in (0, 1)
    """
    n_clusters = cfg.get('n_clusters', DEFAULT_N_CLUSTERS)
    icc = cfg.get('icc', 0.0)
    alpha = cfg.get('alpha', 0.05)

    if icc < 0.0 or icc > 1.0:
        raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")

    if alpha <= 0 or alpha >= 1:
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")

    # Only enforce minimum cluster count if icc > 0
    if icc > 0.0 and n_clusters < 50:
        raise ValueError(
            f"n_clusters ({n_clusters}) must be >= 50 for ICC > 0.0 "
            "to ensure stable variance estimation."
        )


def load_config(cli_args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Load configuration from defaults and optionally override with CLI args.

    This function is a wrapper that handles the initial config state.
    It does NOT parse arguments itself; that is done by parse_cli_args.

    Args:
        cli_args: Optional pre-parsed argparse.Namespace. If None,
                  defaults are returned.

    Returns:
        Dictionary with configuration values.
    """
    cfg = {
        'icc_range': list(ICC_RANGE),
        'icc_step': ICC_STEP,
        'alpha_levels': list(ALPHA_LEVELS),
        'n_clusters': DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': DEFAULT_N_OBS_PER_CLUSTER,
        'seed': DEFAULT_SEED,
        'icc': None,  # Single ICC if specified
        'iterations': 100,
        'alpha': None,  # Single alpha if specified
        'n_permutations': 1000,
        'output_baseline': 'data/derived/baseline_results.csv',
        'output_robust': 'data/derived/robustResults.csv',
        'mode': 'full',  # 'baseline', 'robust', or 'full'
    }

    if cli_args:
        # Only update if the attribute exists in the namespace
        # This handles cases where different scripts pass different args
        for key in cfg:
            cli_key = key.replace('_', '-')
            if hasattr(cli_args, cli_key):
                val = getattr(cli_args, cli_key)
                if val is not None:
                    cfg[key] = val

    return cfg


def parse_cli_args(
    args: Optional[List[str]] = None,
    cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse command-line arguments and update/return a configuration dictionary.

    This function supports multiple calling patterns to accommodate different
    scripts that may pass different subsets of arguments:

    1. parse_cli_args() -> Returns config with defaults
    2. parse_cli_args(args) -> Parses args and returns new config
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no CLI)

    Args:
        args: Optional list of command-line arguments (sys.argv[1:] by default).
             If None, uses sys.argv[1:].
        cfg: Optional existing config dict to update. If None, starts from defaults.

    Returns:
        Updated configuration dictionary.
    """
    # Start with base config
    if cfg is None:
        cfg = load_config()
    else:
        # Ensure cfg has all expected keys (in case caller passed partial dict)
        base = load_config()
        for key, val in base.items():
            if key not in cfg:
                cfg[key] = val

    # If no args provided, just return current config
    if args is None:
        # Check if we're running as main script
        if len(sys.argv) > 1:
            args = sys.argv[1:]
        else:
            return cfg

    # Convert list to Namespace if needed
    if isinstance(args, list):
        parser = argparse.ArgumentParser(
            description='A/B Test Simulation Configuration',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        # Simulation parameters
        parser.add_argument(
            '--icc', type=float, default=None,
            help='Single ICC value to simulate (overrides icc_range)'
        )
        parser.add_argument(
            '--icc-range', type=str, default=None,
            help='Comma-separated ICC values (e.g., "0.0,0.1,0.2")'
        )
        parser.add_argument(
            '--icc-step', type=float, default=None,
            help='Step size for ICC range generation'
        )
        parser.add_argument(
            '--iterations', type=int, default=None,
            help='Number of simulation iterations'
        )
        parser.add_argument(
            '--seed', type=int, default=None,
            help='Random seed for reproducibility'
        )
        parser.add_argument(
            '--n-clusters', type=int, default=None,
            help='Number of clusters'
        )
        parser.add_argument(
            '--n-obs-per-cluster', type=int, default=None,
            help='Number of observations per cluster'
        )
        parser.add_argument(
            '--alpha', type=float, default=None,
            help='Single alpha level (overrides alpha_list)'
        )
        parser.add_argument(
            '--alpha-list', type=str, default=None,
            help='Comma-separated alpha levels (e.g., "0.01,0.05,0.10")'
        )
        parser.add_argument(
            '--n-permutations', type=int, default=None,
            help='Number of permutations for block permutation test'
        )
        parser.add_argument(
            '--output-baseline', type=str, default=None,
            help='Output path for baseline results'
        )
        parser.add_argument(
            '--output-robust', type=str, default=None,
            help='Output path for robust results'
        )
        parser.add_argument(
            '--mode', type=str, default=None,
            choices=['baseline', 'robust', 'full'],
            help='Simulation mode: baseline only, robust only, or both'
        )

        parsed = parser.parse_args(args)
    else:
        # Assume it's already a Namespace
        parsed = args

    # Update config from parsed args
    # Handle icc_range from string
    if parsed.icc_range is not None:
        try:
            cfg['icc_range'] = [float(x.strip()) for x in parsed.icc_range.split(',')]
        except ValueError:
            raise ValueError(f"Invalid icc-range format: {parsed.icc_range}. "
                           "Expected comma-separated numbers.")

    # Handle icc_step
    if parsed.icc_step is not None:
        cfg['icc_step'] = parsed.icc_step

    # Handle alpha_list
    if parsed.alpha_list is not None:
        try:
            cfg['alpha_levels'] = [float(x.strip()) for x in parsed.alpha_list.split(',')]
        except ValueError:
            raise ValueError(f"Invalid alpha-list format: {parsed.alpha_list}. "
                           "Expected comma-separated numbers.")

    # Handle single values (these override list values)
    if parsed.icc is not None:
        cfg['icc'] = parsed.icc
        # If single icc provided, clear icc_range to avoid confusion
        cfg['icc_range'] = [parsed.icc]

    if parsed.alpha is not None:
        cfg['alpha'] = parsed.alpha
        cfg['alpha_levels'] = [parsed.alpha]

    # Update other parameters
    if parsed.iterations is not None:
        cfg['iterations'] = parsed.iterations
    if parsed.seed is not None:
        cfg['seed'] = parsed.seed
    if parsed.n_clusters is not None:
        cfg['n_clusters'] = parsed.n_clusters
    if parsed.n_obs_per_cluster is not None:
        cfg['n_obs_per_cluster'] = parsed.n_obs_per_cluster
    if parsed.n_permutations is not None:
        cfg['n_permutations'] = parsed.n_permutations
    if parsed.output_baseline is not None:
        cfg['output_baseline'] = parsed.output_baseline
    if parsed.output_robust is not None:
        cfg['output_robust'] = parsed.output_robust
    if parsed.mode is not None:
        cfg['mode'] = parsed.mode

    # Validate final config
    validate_config(cfg)

    return cfg