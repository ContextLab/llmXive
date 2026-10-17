"""
Utility configuration module for the asymptotic random matrix project.

This module provides a minimal set of helpers required by various analysis
scripts.  All functions are deliberately lightweight and have no external
dependencies beyond the Python standard library and the packages that are
already available in the execution environment (numpy, etc.).
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional

# ----------------------------------------------------------------------
# Default configuration constants
# ----------------------------------------------------------------------
# Tolerance used by the outlier detection rule (FR‑004):
# an eigenvalue is considered an outlier if it exceeds the empirical bulk
# edge by more than this amount.
DEFAULT_OUTLIER_TOLERANCE: float = 0.05

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_outlier_tolerance() -> float:
    """
    Return the outlier tolerance used throughout the pipeline.

    The value can be overridden by the environment variable
    ``OUTLIER_TOLERANCE``; otherwise the default ``0.05`` is returned.
    """
    env_val = os.getenv("OUTLIER_TOLERANCE")
    if env_val is not None:
        try:
            return float(env_val)
        except ValueError:
            # Fallback to default if the environment variable is malformed.
            pass
    return DEFAULT_OUTLIER_TOLERANCE

def ensure_directories(base_path: Optional[Path] = None) -> None:
    """
    Create the standard project data directories if they do not already exist.

    Parameters
    ----------
    base_path : pathlib.Path, optional
        The root of the project. If ``None`` the current working directory
        is used.
    """
    root = Path(base_path) if base_path is not None else Path.cwd()
    for sub in [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "logs",
        root / "data" / "figures",
    ]:
        sub.mkdir(parents=True, exist_ok=True)

def get_project_paths(base_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Return a dictionary with the most common project‑relative paths.

    The keys match the ones used by the existing analysis scripts:

    - ``processed``   → ``data/processed``
    - ``figures``     → ``data/figures``
    - ``raw``         → ``data/raw``
    - ``data_logs``   → ``data/logs``

    Parameters
    ----------
    base_path : pathlib.Path, optional
        Base directory of the project. If omitted, ``Path.cwd()`` is used.

    Returns
    -------
    dict
        Mapping from logical name to absolute ``Path`` objects.
    """
    root = Path(base_path) if base_path is not None else Path.cwd()
    return {
        "processed": root / "data" / "processed",
        "figures": root / "data" / "figures",
        "raw": root / "data" / "raw",
        "data_logs": root / "data" / "logs",
    }

def get_seed() -> int:
    """
    Generate a random seed for Monte‑Carlo runs.

    The function reads the environment variable ``BASE_SEED``; if it is not
    set, a fresh random 32‑bit integer is produced.  This helper is used by
    the sensitivity‑analysis scripts to obtain a reproducible starting point.
    """
    env_seed = os.getenv("BASE_SEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            pass
    # ``random`` is seeded from system entropy, which is acceptable for
    # generating a fresh base seed.
    return random.randint(0, 2**31 - 1)
