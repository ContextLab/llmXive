"""
Configuration module for the A/B test statistical significance simulation.

Defines simulation parameters, validation logic, and utility functions for
managing random seeds and configuration dictionaries.
"""

import argparse
import numpy as np
from typing import Dict, Any, List


# Simulation Parameters
ICC_RANGE: List[float] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
ICC_STEP: float = 0.1
ALPHA_LEVELS: List[float] = [0.01, 0.05, 0.10]
DEFAULT_N_CLUSTERS: int = 100
DEFAULT_SEED: int = 42


def set_seed(seed: int) -> None:
    """
    Sets the random seed for numpy.

    Args:
        seed: The integer seed to use for the random number generator.
    """
    np.random.seed(seed)


def load_config() -> Dict[str, Any]:
    """
    Loads and returns the default configuration dictionary.

    Returns:
        A dictionary containing default simulation parameters.
    """
    return {
        "icc_range": ICC_RANGE,
        "icc_step": ICC_STEP,
        "alpha_levels": ALPHA_LEVELS,
        "n_clusters": DEFAULT_N_CLUSTERS,
        "seed": DEFAULT_SEED,
    }


def validate_config(cfg: Dict[str, Any]) -> None:
    """
    Validates the configuration dictionary.

    Raises:
        ValueError: If the configuration is invalid. Specifically, raises an error
                    if n_clusters < 50 unless the ICC is exactly 0.0 (independent data).
    """
    n_clusters = cfg.get("n_clusters", DEFAULT_N_CLUSTERS)
    icc = cfg.get("icc", 0.0)

    if n_clusters < 50 and icc != 0.0:
        raise ValueError(
            f"Configuration invalid: n_clusters ({n_clusters}) must be >= 50 "
            f"unless icc is 0.0. Found icc={icc}."
        )

    # Optional: Validate ICC range if present
    if "icc_range" in cfg:
        for val in cfg["icc_range"]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Invalid ICC value in range: {val}. Must be between 0.0 and 1.0.")


def parse_cli_args() -> Dict[str, Any]:
    """
    Parses command-line arguments and updates the configuration dictionary.

    This function satisfies FR-001 user configurability by allowing users to
    specify a custom ICC range and step size via CLI flags, and FR-005 by
    allowing custom alpha levels.

    CLI Arguments:
        --icc-range: Comma-separated list of floats representing the ICC values to test.
        --icc-step: Float representing the step size for generating the ICC range if not explicitly provided.
        --alpha-list: Comma-separated list of floats representing the significance levels (alpha) to test.

    Returns:
        A dictionary containing the configuration with potentially overridden ICC range, step, and alpha levels.
    """
    cfg = load_config()

    parser = argparse.ArgumentParser(
        description="A/B Test Statistical Significance Simulation Configuration"
    )
    parser.add_argument(
        "--icc-range",
        type=str,
        default=None,
        help="Comma-separated list of ICC values (e.g., '0.0,0.2,0.4'). Overrides default ICC_RANGE."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC values. Overrides default ICC_STEP."
    )
    parser.add_argument(
        "--alpha-list",
        type=str,
        default=None,
        help="Comma-separated list of alpha levels (e.g., '0.01,0.05,0.10'). Overrides default ALPHA_LEVELS."
    )

    args = parser.parse_args()

    if args.icc_range is not None:
        try:
            icc_list = [float(x.strip()) for x in args.icc_range.split(",")]
            cfg["icc_range"] = icc_list
        except ValueError:
            raise ValueError(f"Invalid ICC range format: {args.icc_range}. Must be comma-separated floats.")

    if args.icc_step is not None:
        cfg["icc_step"] = args.icc_step

    if args.alpha_list is not None:
        try:
            alpha_list = [float(x.strip()) for x in args.alpha_list.split(",")]
            # Validate alpha values are between 0 and 1
            for val in alpha_list:
                if not (0.0 < val < 1.0):
                    raise ValueError(f"Invalid alpha value: {val}. Must be between 0 and 1 (exclusive).")
            cfg["alpha_levels"] = alpha_list
        except ValueError as e:
            raise ValueError(f"Invalid alpha list format: {args.alpha_list}. Must be comma-separated floats between 0 and 1.") from e

    return cfg
