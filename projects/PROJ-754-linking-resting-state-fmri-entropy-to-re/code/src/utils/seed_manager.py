"""
Seed Manager for Deterministic Reproducibility.

This module centralizes random seed configuration to ensure reproducible
results across all stochastic operations in the pipeline. It sets seeds
for Python's built-in random module, NumPy, and sets the environment
variable PYTHONHASHSEED.

Usage:
    Import and call `set_seed(42)` at the very beginning of any script
    that performs stochastic operations (e.g., T012, T020, T029).
"""

import os
import random
import sys

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across the entire pipeline.

    This function:
    1. Sets the PYTHONHASHSEED environment variable before hashing operations.
    2. Sets the seed for Python's built-in `random` module.
    3. Sets the seed for `numpy.random`.

    Args:
        seed (int): The integer seed value to use. Defaults to 42.

    Raises:
        TypeError: If seed is not an integer.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed).__name__}")

    # Set environment variable for hash randomization (must be set before imports that use hashing)
    # Note: In some environments, setting this after the interpreter starts might not affect
    # already initialized hash states, but it ensures consistency for subprocesses and
    # future hashing operations.
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Set seed for Python's built-in random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Optional: If torch were used, we would set torch.manual_seed(seed) here
    # But per requirements, we are CPU-only and using specific libraries.

    # Log the action if a logger is available (optional, non-blocking)
    # We avoid importing logging_config here to prevent circular dependencies
    # if this module is imported early.
    try:
        from src.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info(f"Random seeds set to {seed} for reproducibility.")
    except ImportError:
        # If logging is not yet configured, silently proceed
        pass


def main() -> None:
    """
    CLI entry point for setting seeds.
    Useful for testing or standalone execution to verify environment setup.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Set random seeds for deterministic pipeline execution."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed value (default: 42)"
    )

    args = parser.parse_args()

    set_seed(args.seed)

    # Verify the settings
    print(f"Seed set to: {args.seed}")
    print(f"PYTHONHASHSEED: {os.environ.get('PYTHONHASHSEED')}")
    print(f"random.getstate()[1][0]: {random.getstate()[1][0]}")
    print(f"numpy.random.get_state()[1][0]: {np.random.get_state()[1][0]}")


if __name__ == "__main__":
    main()