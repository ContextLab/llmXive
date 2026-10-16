"""
Seed management utility for reproducible experiments.

This module provides a centralized way to pin and manage all random states
across the project to ensure reproducibility. It sets seeds for Python's
``random`` module, NumPy, and (if installed) PyTorch. The global seed can be
retrieved and the current NumPy ``RandomState`` accessed for downstream
code that requires explicit control.
"""
import os
import random
from typing import Dict, Any

import numpy as np

# Global seed value for the project (default)
_PROJECT_SEED = 42
_RANDOM_STATE = np.random.RandomState(_PROJECT_SEED)


def get_seed() -> int:
    """
    Get the global project seed.

    Returns:
        int: The global seed value (default 42).
    """
    return _PROJECT_SEED


def set_seed(seed: int) -> None:
    """
    Set the global project seed and re‑initialize all random generators.

    This function:
    * Sets the seed for the built‑in ``random`` module.
    * Sets the seed for NumPy's legacy ``RandomState`` as well as the
      newer ``numpy.random`` generator.
    * Sets the ``PYTHONHASHSEED`` environment variable (used by some
      libraries such as PyTorch to obtain deterministic hashing).
    * If PyTorch is available, sets its global seed (both CPU and CUDA).

    Args:
        seed (int): The seed value to use.
    """
    global _PROJECT_SEED, _RANDOM_STATE

    _PROJECT_SEED = seed

    # Seed Python's random module
    random.seed(seed)

    # Seed NumPy's random generators
    np.random.seed(seed)
    _RANDOM_STATE = np.random.RandomState(seed)

    # Environment variable for libraries that respect it
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Optional PyTorch seeding – ignored if torch is not installed
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # PyTorch not installed; nothing to do
        pass


def get_random_state() -> np.random.RandomState:
    """
    Get the current global NumPy ``RandomState`` object.

    Returns:
        np.random.RandomState: The current random state.
    """
    return _RANDOM_STATE


def set_random_state(state: np.random.RandomState) -> None:
    """
    Replace the global NumPy ``RandomState`` with a user‑provided one.

    Args:
        state (np.random.RandomState): The random state to use.
    """
    global _RANDOM_STATE
    _RANDOM_STATE = state


def get_seed_config() -> Dict[str, Any]:
    """
    Return a dictionary summarising the current seed configuration.

    Includes the project seed, the NumPy seed, the Python ``random`` seed,
    and, if PyTorch is available, the current PyTorch seed.

    Returns:
        dict: Mapping of seed‑related settings.
    """
    config = {
        "project_seed": _PROJECT_SEED,
        "numpy_seed": _RANDOM_STATE.get_state()[1][0],
        "python_seed": random.getstate()[1][0],
    }

    # Attempt to include PyTorch seed information
    try:
        import torch

        config["torch_seed"] = torch.initial_seed()
    except ImportError:
        # PyTorch not installed – omit from the config
        pass

    return config


def init_seed(seed: int = None) -> Dict[str, Any]:
    """
    Initialise all random seeds and return the configuration.

    This is the main entry point for setting up reproducibility at the
    start of any experiment or script.

    Args:
        seed (int, optional): The seed to initialise with. If ``None`` the
            previously‑set global seed is used.

    Returns:
        dict: The seed configuration after initialisation.
    """
    if seed is None:
        seed = _PROJECT_SEED
    set_seed(seed)
    return get_seed_config()