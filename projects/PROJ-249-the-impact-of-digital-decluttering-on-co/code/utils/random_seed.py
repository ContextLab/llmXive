"""
Random seed management utility for reproducibility.

This module provides a centralized way to manage random seeds across
all components of the study to ensure experimental reproducibility.
"""

import os
import random
from pathlib import Path
from typing import Optional, Union

import numpy as np

# Default seed value if none is provided
DEFAULT_SEED = 42
SEED_ENV_VAR = "DIGITAL_DECLUTTER_SEED"


def get_seed(seed: Optional[int] = None) -> int:
    """
    Retrieve the random seed to use.

    Priority order:
    1. Explicitly provided seed argument
    2. Environment variable `DIGITAL_DECLUTTER_SEED`
    3. Default value (42)

    Args:
        seed: Optional integer seed value.

    Returns:
        The integer seed to use.
    """
    if seed is not None:
        return seed

    env_seed = os.environ.get(SEED_ENV_VAR)
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            raise ValueError(
                f"Invalid seed value in environment variable {SEED_ENV_VAR}: "
                f"'{env_seed}' is not an integer."
            )

    return DEFAULT_SEED


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed globally for reproducibility.

    This function sets the seed for:
    - Python's built-in `random` module
    - NumPy's random number generator

    Args:
        seed: Optional integer seed value. If None, uses get_seed().

    Returns:
        The seed value that was set.
    """
    actual_seed = get_seed(seed)

    random.seed(actual_seed)
    np.random.seed(actual_seed)

    return actual_seed


def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Create a new NumPy random Generator instance with the specified seed.

    This is the preferred method for obtaining random numbers in new code,
    as it allows for isolated random number streams.

    Args:
        seed: Optional integer seed value. If None, uses get_seed().

    Returns:
        A NumPy Generator instance seeded with the provided value.
    """
    actual_seed = get_seed(seed)
    return np.random.default_rng(actual_seed)


def save_seed_config(seed: int, output_path: Union[str, Path]) -> None:
    """
    Save the seed configuration to a file for auditability.

    Args:
        seed: The seed value to save.
        output_path: Path to the output file (e.g., 'data/processed/seed_config.json').
    """
    import json

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "seed": seed,
        "environment_variable": SEED_ENV_VAR,
        "default_seed": DEFAULT_SEED
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def load_seed_config(input_path: Union[str, Path]) -> dict:
    """
    Load seed configuration from a file.

    Args:
        input_path: Path to the input file.

    Returns:
        Dictionary containing the seed configuration.
    """
    import json

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Seed configuration file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)