"""
Configuration module for the A/B test statistical significance simulation.

Defines simulation parameters, validation logic, and seed management.
"""
import numpy as np
import argparse
from typing import Dict, Any, List

# Simulation Constants
ICC_RANGE: List[float] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP: float = 0.1
ALPHA_LEVELS: List[float] = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS: int = 100
DEFAULT_SEED: int = 42

def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.

    Args:
        seed: The integer seed value.
    """
    np.random.seed(seed)

def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary.

    Raises:
        ValueError: If 'n_clusters' is less than 50 unless 'icc' is exactly 0.0.
    """
    n_clusters = cfg.get('n_clusters', DEFAULT_N_CLUSTERS)
    icc = cfg.get('icc', 0.0)

    if n_clusters < 50 and icc != 0.0:
        raise ValueError(
            f"Configuration invalid: n_clusters ({n_clusters}) must be >= 50 "
            f"when icc ({icc}) is non-zero to ensure statistical power for "
            f"cluster-robust estimators."
        )

def load_config() -> Dict[str, Any]:
    """
    Load the default configuration dictionary.

    Returns:
        A dictionary containing the default simulation parameters.
    """
    return {
        'icc_range': ICC_RANGE,
        'icc_step': ICC_STEP,
        'alpha_levels': ALPHA_LEVELS,
        'n_clusters': DEFAULT_N_CLUSTERS,
        'seed': DEFAULT_SEED,
        'icc': 0.0,  # Default ICC for single-run contexts if not overridden
    }

def parse_cli_args() -> Dict[str, Any]:
    """
    Parse command-line arguments to override default configuration.

    Supports:
        --icc-range: Comma-separated list of ICC values (e.g., 0.0,0.1,0.2)
        --icc-step: Float step size for generating ICC range if not provided explicitly.
        --alpha-list: Comma-separated list of alpha levels (e.g., 0.01,0.05,0.10).

    Returns:
        A dictionary containing the configuration, potentially overridden by CLI args.
    """
    parser = argparse.ArgumentParser(
        description="Configuration for A/B test simulation with cluster effects."
    )
    parser.add_argument(
        '--icc-range',
        type=str,
        default=None,
        help="Comma-separated list of ICC values (e.g., '0.0,0.1,0.2'). "
             "Overrides ICC_RANGE constant if provided."
    )
    parser.add_argument(
        '--icc-step',
        type=float,
        default=None,
        help="Step size for generating ICC range (e.g., 0.1). "
             "Overrides ICC_STEP constant if provided. "
             "If --icc-range is not provided, this is used to generate the range from 0.0 to 0.5."
    )
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=None,
        help="Comma-separated list of alpha levels (e.g., '0.01,0.05,0.10'). "
             "Overrides ALPHA_LEVELS constant if provided."
    )

    args = parser.parse_args()

    cfg = load_config()

    # Handle ICC Range
    if args.icc_range:
        try:
            # Parse comma-separated string into a list of floats
            icc_list = [float(x.strip()) for x in args.icc_range.split(',')]
            if not icc_list:
                raise ValueError("ICC range list cannot be empty.")
            cfg['icc_range'] = sorted(list(set(icc_list))) # Ensure unique and sorted
        except ValueError as e:
            raise ValueError(f"Invalid format for --icc-range: {e}")
    elif args.icc_step is not None:
        # If step is provided but range is not, generate range from 0.0 to 0.5
        # Using a reasonable upper bound of 0.5 as per default constants
        start = 0.0
        end = 0.5
        current = start
        generated_range = []
        while current <= end + 1e-9: # Floating point tolerance
            generated_range.append(round(current, 2))
            current += args.icc_step
        cfg['icc_range'] = generated_range
        cfg['icc_step'] = args.icc_step
    elif args.icc_step is not None:
        # If only step is provided without range, we might need to infer range or just update step
        # The logic above covers the case where step is provided to generate range.
        # If range was provided via default, we just update the step if explicitly passed.
        cfg['icc_step'] = args.icc_step

    # Handle Alpha Levels
    if args.alpha_list:
        try:
            alpha_list = [float(x.strip()) for x in args.alpha_list.split(',')]
            if not alpha_list:
                raise ValueError("Alpha list cannot be empty.")
            # Validate that all alpha values are between 0 and 1
            for alpha in alpha_list:
                if not (0 < alpha < 1):
                    raise ValueError(f"Alpha value {alpha} must be between 0 and 1.")
            cfg['alpha_levels'] = sorted(alpha_list)
        except ValueError as e:
            raise ValueError(f"Invalid format for --alpha-list: {e}")

    return cfg