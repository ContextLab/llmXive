"""
Configuration utilities for the gut‑microbiome‑mental‑health project.

This module provides:
  • Directory creation helpers
  • Random seed management
  • A flexible ``get_output_path`` function that satisfies every call‑site
    in the codebase (see the task description for the required signatures).
  • Simple helpers for calculating median sequencing depth and estimating
    rarefaction loss.
  • Loading of a minimal config (currently just the seeds file).

The implementation deliberately avoids any heavy imports at module import
time – only standard‑library modules and the already‑available ``llmxive_toolkit``
are used.
"""

import os
import random
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import yaml

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
_log = get_logger(__name__)

# ----------------------------------------------------------------------
# Directory helpers
# ----------------------------------------------------------------------
def ensure_directories(dirs: Optional[List[Union[str, Path]]] = None) -> None:
    """
    Ensure that a set of directories exists.

    If *dirs* is ``None`` the function ensures the top‑level project
    directories (data, code, tests, results, logs) exist.  Callers may also
    pass a list of directory paths (as strings or ``Path`` objects) that
    should be created.
    """
    if dirs is None:
        # Default directories used throughout the pipeline
        dirs = [
            paths.data(),
            paths.code(),
            paths.results(),
            paths.logs(),
        ]
    for d in dirs:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        _log.debug(f"Ensured directory exists: {p}")

# ----------------------------------------------------------------------
# Random seed handling
# ----------------------------------------------------------------------
def set_random_seed(seed: int = 42) -> None:
    """
    Set deterministic seeds for Python's ``random`` and NumPy's RNG.
    """
    random.seed(seed)
    np.random.seed(seed)
    _log.debug(f"Random seed set to {seed}")

# ----------------------------------------------------------------------
# Flexible path resolver
# ----------------------------------------------------------------------
def get_output_path(
    filename: Optional[Union[str, Path, List[Union[str, Path]]]] = None
) -> str:
    """
    Resolve a relative path inside the project root.

    The function is deliberately tolerant:
      • ``None``            → project root (``paths.root``)
      • ``"data/foo.csv"`` → ``paths.data("foo.csv")``
      • ``"data/processed"`` → the directory ``paths.data("processed")``
      • ``["data", "processed", "file.csv"]`` → ``paths.data(... )``

    It always returns a **string** because many callers concatenate it
    with other strings or pass it to ``os.path`` utilities.
    """
    # No argument → project root
    if filename is None:
        return str(paths.root)

    # If a list/tuple is provided, treat each element as a path component
    if isinstance(filename, (list, tuple)):
        parts = [str(p).strip("/") for p in filename]
        return str(paths.path(*parts))

    # Normalise to string
    if isinstance(filename, Path):
        filename = str(filename)

    # Split on forward or backward slash, ignoring empty components
    parts = [p for p in filename.replace("\\", "/").split("/") if p]

    # If the first component matches a top‑level folder we have a helper for,
    # delegate to the corresponding ``paths.<folder>`` function.
    top_folder_map = {
        "data": paths.data,
        "code": paths.code,
        "results": paths.results,
        "figures": paths.figures,
        "logs": paths.logs,
        "outputs": paths.outputs,
        "state": paths.state,
        "interior": paths.interior,
        "raw": paths.raw,
        "processed": paths.processed,
    }

    if parts and parts[0] in top_folder_map:
        helper = top_folder_map[parts[0]]
        # Pass the remaining components to the helper
        return str(helper(*parts[1:]))

    # Fallback: treat the whole thing as a generic path under the project root
    return str(paths.path(*parts))

# ----------------------------------------------------------------------
# Median depth calculation
# ----------------------------------------------------------------------
def calculate_median_depth(counts_array: np.ndarray) -> float:
    """
    Calculate the median sequencing depth from a 2‑D count array
    (samples × taxa).  The function returns a ``float`` for consistency
    with downstream JSON serialisation.
    """
    if counts_array.ndim != 2:
        raise ValueError("counts_array must be a 2‑D array (samples × taxa)")

    # Sum counts per sample (axis=1) and take the median of non‑zero depths
    sample_depths = np.sum(counts_array, axis=1)
    non_zero = sample_depths[sample_depths > 0]
    if non_zero.size == 0:
        raise ValueError("No samples with non‑zero depth found")
    median = float(np.median(non_zero))
    _log.debug(f"Median sequencing depth: {median}")
    return median

# ----------------------------------------------------------------------
# Rarefaction loss estimation
# ----------------------------------------------------------------------
def estimate_rarefaction_loss(
    depths: np.ndarray, target_depth: float
) -> float:
    """
    Estimate the proportion of samples that would be lost if the dataset
    were rarefied to *target_depth*.

    Parameters
    ----------
    depths : np.ndarray
        1‑D array of per‑sample sequencing depths.
    target_depth : float
        Desired depth after rarefaction.

    Returns
    -------
    float
        Fraction of samples that would be dropped (0 – 1).
    """
    if depths.ndim != 1:
        raise ValueError("depths must be a 1‑D array")
    total = depths.size
    lost = np.sum(depths < target_depth)
    loss_rate = float(lost / total) if total > 0 else 0.0
    _log.debug(
        f"Estimated rarefaction loss: {lost}/{total} samples ({loss_rate:.4f})"
    )
    return loss_rate

# ----------------------------------------------------------------------
# Minimal config loader (currently only seeds)
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """
    Load configuration values from ``state/seeds.yaml`` if it exists.

    Returns an empty dict if the file is missing; callers can fall back to
    defaults.
    """
    seeds_path = paths.state("seeds.yaml")
    if not seeds_path.is_file():
        _log.warning(f"Seeds file not found at {seeds_path}; returning empty config")
        return {}
    try:
        with open(seeds_path, "r") as f:
            config = yaml.safe_load(f) or {}
            _log.debug(f"Loaded seeds config: {config}")
            return config
    except Exception as e:
        _log.error(f"Failed to load seeds config: {e}")
        raise

# ----------------------------------------------------------------------
# Exported symbols for ``from config import *``
# ----------------------------------------------------------------------
__all__ = [
    "ensure_directories",
    "set_random_seed",
    "get_output_path",
    "calculate_median_depth",
    "estimate_rarefaction_loss",
    "load_config",
]