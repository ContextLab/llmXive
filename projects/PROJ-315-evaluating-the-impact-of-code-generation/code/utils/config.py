"""
Configuration management for the research pipeline.

Handles environment variables, random seed pinning, and global settings.
Ensures reproducibility by pinning seeds for numpy, pandas, and the
standard library random module. Provides both the original API used by the
existing codebase and the newly‑required API for task T002.
"""
import os
import random
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import sklearn

# ----------------------------------------------------------------------
# Existing public API (used by other modules)
# ----------------------------------------------------------------------
DEFAULT_SEED = 42

def get_seed() -> int:
    """
    Retrieve the random seed from the RESEARCH_SEED environment variable,
    falling back to ``DEFAULT_SEED`` if the variable is absent or malformed.
    """
    seed_str = os.getenv("RESEARCH_SEED", str(DEFAULT_SEED))
    try:
        return int(seed_str)
    except ValueError:
        return DEFAULT_SEED

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility across the pipeline.

    This function is retained for backward compatibility with the rest of
    the codebase. It delegates to :func:`set_seed` after resolving the
    final seed value.
    """
    if seed is None:
        seed = get_seed()
    set_seed(seed)

def load_config_from_env() -> Dict[str, Any]:
    """
    Load a dictionary of configuration values from environment variables.

    Returns
    -------
    dict
        Mapping of configuration keys to their values. Keys correspond to
        those used throughout the project (see ``load_config`` below).
    """
    return {
        "seed": get_seed(),
        "data_path": os.getenv("DATA_PATH", "data/raw"),
        "output_path": os.getenv("OUTPUT_PATH", "data/processed"),
        "min_group_size": int(os.getenv("MIN_GROUP_SIZE", "500")),
        "completeness_threshold": float(os.getenv("COMPLETENESS_THRESHOLD", "0.95")),
        "multiple_comparison_method": os.getenv(
            "MULTIPLE_COMPARISON_METHOD", "bonferroni"
        ),
    }

# ----------------------------------------------------------------------
# New API required by task T002
# ----------------------------------------------------------------------
def load_config() -> Dict[str, str]:
    """
    Return a dictionary containing *all* current environment variables.

    The function purposefully mirrors the specification for T002,
    which asks for a simple ``load_config()`` that returns a dict of
    environment variables. No filtering or type conversion is performed;
    the raw string values are returned.

    Returns
    -------
    dict
        Mapping of environment variable names to their string values.
    """
    # ``os.environ`` behaves like a dict but returns a live view; we copy
    # it to avoid accidental mutation by callers.
    return dict(os.environ)

def set_seed(seed: int = 42) -> None:
    """
    Set deterministic random seeds for the standard library ``random``,
    NumPy, pandas (via NumPy), and scikit‑learn.

    Parameters
    ----------
    seed : int, optional
        Seed value to use. Defaults to ``42`` as required by the task.
    """
    # Python's built‑in random module
    random.seed(seed)

    # NumPy – the primary source of randomness for pandas and scikit‑learn
    np.random.seed(seed)

    # Pandas does not have its own RNG; it relies on NumPy.  We silence the
    # ``SettingWithCopyWarning`` here because the original implementation
    # used this pattern.
    pd.options.mode.chained_assignment = None

    # Scikit‑learn utilities that expose a global random_state attribute.
    # This is defensive; most sklearn estimators respect ``np.random``.
    if hasattr(sklearn, "random_state"):
        sklearn.random_state = seed

    # Log the action for traceability.
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Global seed set to {seed}")

# ----------------------------------------------------------------------
# Backwards‑compatibility aliases (optional but harmless)
# ----------------------------------------------------------------------
# Some older scripts may still import ``set_global_seed`` expecting the
# original name.  The definition above already forwards to ``set_seed``.
# No further action is required.