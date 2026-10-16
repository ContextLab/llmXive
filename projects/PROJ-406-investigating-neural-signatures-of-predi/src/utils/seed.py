"""
Utility module to set a global random seed for reproducibility across the
project. It seeds the Python built‑in ``random`` module, NumPy's RNG, and
the environment variable controlling hash randomisation.
This ensures that importing the ``src`` package (which calls
``set_global_seed``) produces identical NumPy random outputs across
separate test runs, satisfying the deterministic‑seed verification tests.
"""
import os
import random
import numpy as np

DEFAULT_SEED = 42

def set_global_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set the global random seed for deterministic behaviour.

    Parameters
    ----------
    seed : int, optional
        The seed value to use. Defaults to ``DEFAULT_SEED`` (42).

    This function:
    * Sets ``PYTHONHASHSEED`` to ensure deterministic hashing.
    * Seeds the ``random`` module.
    * Seeds NumPy's random generator.
    """
    # Ensure the hash seed is deterministic (must be set before any import that uses hashing)
    os.environ["PYTHONHASHSEED"] = str(seed)

    random.seed(seed)
    np.random.seed(seed)