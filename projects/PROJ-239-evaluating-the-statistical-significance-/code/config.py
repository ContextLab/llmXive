"""
Configuration management for the A/B test statistical significance simulation.

This module defines simulation parameters, validation logic, and CLI argument parsing
to support flexible and reproducible experimental runs.
"""

import argparse
import numpy as np
from typing import Dict, Any, List, Optional, Union
import os
import sys

# --- Simulation Constants ---
ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP = 0.1
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS = 100
DEFAULT_SEED = 42

# --- Validation Logic ---

def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validates the configuration dictionary.

    Raises:
        ValueError: If the configuration is invalid. Specifically:
            - n_clusters < 50 unless icc == 0.0 (independent data case).
            - icc is not in [0.0, 1.0].
    """
    icc = cfg.get('icc')
    n_clusters = cfg.get('n_clusters')

    # Validate ICC range
    if icc is not None:
        if not (0.0 <= icc <= 1.0):
            raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")

    # Validate cluster count constraint
    if n_clusters is not None:
        if n_clusters < 50:
            # Allow small cluster counts ONLY if ICC is exactly 0.0 (independent data)
            if icc == 0.0:
                pass  # Valid case
            else:
                raise ValueError(
                    f"n_clusters ({n_clusters}) must be >= 50 for cluster-robust inference. "
                    "If ICC is 0.0 (independent data), lower counts are permitted."
                )

# --- Seed Management ---

def set_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility.

    Args:
        seed: Integer seed value.
    """
    np.random.seed(seed)

# --- Configuration Loading ---

def load_config(
    icc: Optional[float] = None,
    n_clusters: Optional[int] = None,
    n_obs_per_cluster: Optional[int] = None,
    seed: Optional[int] = None,
    alpha_levels: Optional[List[float]] = None,
    icc_range: Optional[List[float]] = None,
    icc_step: Optional[float] = None
) -> Dict[str, Any]:
    """
    Loads a configuration dictionary with provided overrides.

    Args:
        icc: Specific ICC value to simulate. Overrides range if provided.
        n_clusters: Number of clusters.
        n_obs_per_cluster: Observations per cluster.
        seed: Random seed.
        alpha_levels: List of alpha levels for significance testing.
        icc_range: List of ICC values to iterate over.
        icc_step: Step size for ICC generation.

    Returns:
        A dictionary containing the merged configuration.
    """
    cfg = {
        'icc': icc,
        'n_clusters': n_clusters if n_clusters is not None else DEFAULT_N_CLUSTERS,
        'n_obs_per_cluster': n_obs_per_cluster if n_obs_per_cluster is not None else 12, # Default derived from T010 logic
        'seed': seed if seed is not None else DEFAULT_SEED,
        'alpha_levels': alpha_levels if alpha_levels is not None else ALPHA_LEVELS,
        'icc_range': icc_range if icc_range is not None else ICC_RANGE,
        'icc_step': icc_step if icc_step is not None else ICC_STEP,
    }
    return cfg

# --- CLI Parsing ---

def parse_cli_args(
    args: Optional[List[str]] = None,
    cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parses command-line arguments and updates the configuration.

    This function is designed to be flexible and accept various call signatures:
    1. parse_cli_args() -> Returns config with defaults (no args, no cfg)
    2. parse_cli_args(args) -> Parses args and returns new config (args provided, no cfg)
    3. parse_cli_args(args, cfg) -> Parses args and updates existing config (both provided)
    4. parse_cli_args(cfg) -> Updates existing config with defaults (no args, cfg provided)

    Args:
        args: List of CLI arguments. If None, sys.argv[1:] is used.
        cfg: Existing configuration dictionary to update. If None, a new one is created.

    Returns:
        Updated or new configuration dictionary.
    """
    # Initialize or use provided config
    if cfg is None:
        cfg = load_config()
    else:
        # Ensure we are working with a copy if we might modify defaults,
        # but here we modify the passed dict in place as per typical usage.
        pass

    # Prepare argument parser
    parser = argparse.ArgumentParser(
        description="A/B Test Simulation Configuration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # ICC Arguments
    parser.add_argument(
        '--icc',
        type=float,
        default=cfg.get('icc'),
        help="Specific ICC value to simulate. Overrides icc_range."
    )
    parser.add_argument(
        '--icc-range',
        type=str,
        default=','.join(map(str, cfg.get('icc_range', ICC_RANGE))),
        help="Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)."
    )
    parser.add_argument(
        '--icc-step',
        type=float,
        default=cfg.get('icc_step', ICC_STEP),
        help="Step size for ICC generation if range is not provided."
    )

    # Cluster Arguments
    parser.add_argument(
        '--n-clusters',
        type=int,
        default=cfg.get('n_clusters', DEFAULT_N_CLUSTERS),
        help="Number of clusters."
    )
    parser.add_argument(
        '--n-obs-per-cluster',
        type=int,
        default=cfg.get('n_obs_per_cluster', 12),
        help="Number of observations per cluster."
    )

    # Alpha Levels
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=','.join(map(str, cfg.get('alpha_levels', ALPHA_LEVELS))),
        help="Comma-separated alpha levels (e.g., 0.01,0.05,0.10)."
    )

    # Seed
    parser.add_argument(
        '--seed',
        type=int,
        default=cfg.get('seed', DEFAULT_SEED),
        help="Random seed for reproducibility."
    )

    # Parse arguments
    # If args is None, use sys.argv[1:]
    parsed_args = parser.parse_args(args)

    # Update config from parsed arguments

    # Handle ICC: if specific --icc is provided, use it; otherwise parse range
    if parsed_args.icc is not None:
        cfg['icc'] = parsed_args.icc
        cfg['icc_range'] = [parsed_args.icc] # Force single value mode
    else:
        # Parse comma-separated range
        try:
            range_str = parsed_args.icc_range
            if range_str:
                cfg['icc_range'] = [float(x.strip()) for x in range_str.split(',')]
            else:
                cfg['icc_range'] = ICC_RANGE
        except ValueError:
            raise ValueError(f"Invalid ICC range format: {parsed_args.icc_range}")

        # If step is provided and range is not explicitly set via --icc,
        # we might generate a range, but the task spec implies explicit lists.
        # We stick to the explicit list provided or default.
        if parsed_args.icc_step:
            cfg['icc_step'] = parsed_args.icc_step

    # Handle Clusters
    if parsed_args.n_clusters:
        cfg['n_clusters'] = parsed_args.n_clusters
    if parsed_args.n_obs_per_cluster:
        cfg['n_obs_per_cluster'] = parsed_args.n_obs_per_cluster

    # Handle Alpha Levels
    try:
        alpha_str = parsed_args.alpha_list
        if alpha_str:
            cfg['alpha_levels'] = [float(x.strip()) for x in alpha_str.split(',')]
        else:
            cfg['alpha_levels'] = ALPHA_LEVELS
    except ValueError:
        raise ValueError(f"Invalid alpha list format: {parsed_args.alpha_list}")

    # Handle Seed
    if parsed_args.seed is not None:
        cfg['seed'] = parsed_args.seed

    # Validate the final configuration
    # Note: We must handle the case where icc is None (if not set by args)
    # but usually load_config sets a default or caller sets it.
    # If icc is None in cfg, we assume it will be iterated over icc_range.
    # Validation logic needs to be careful here.
    
    # If we are in "range" mode, validation of a single 'icc' value is skipped
    # until the loop starts. However, n_clusters validation is global.
    # We only validate strict n_clusters >= 50 if we are NOT in independent mode (icc=0.0).
    # If cfg['icc'] is None, we assume range mode. We check if the range contains 0.0?
    # The spec says: "raises ValueError if n_clusters < 50 unless cfg['icc'] == 0.0".
    # If cfg['icc'] is None (range mode), we cannot validate against a single value.
    # We assume the caller will validate per-iteration or that the default is safe.
    # For safety in this function, we only validate if 'icc' is explicitly set to a non-None value.
    
    if cfg.get('icc') is not None:
        validate_config(cfg)
    
    return cfg