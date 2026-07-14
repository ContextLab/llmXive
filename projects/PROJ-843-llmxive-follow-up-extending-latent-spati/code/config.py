"""
Configuration utilities for the project.

This module defines helper functions that expose standard directory
locations (raw, processed, stratified, features, results, figures) and
also provides a flexible ``ensure_directories`` implementation that can
be called in a variety of ways throughout the code‑base:

* ``ensure_directories()`` – creates all standard project directories.
* ``ensure_directories(Path)`` – creates a single custom directory.
* ``ensure_directories([Path, Path, ...])`` – creates a list of directories.

The function is deliberately tolerant: any ``None`` values or objects that
are not ``Path`` instances are ignored, which prevents ``AttributeError``
in callers that pass heterogeneous arguments.
"""

import os
from pathlib import Path
from typing import Iterable, List, Union, Any

# ----------------------------------------------------------------------
# Directory getters – these are used across the repository
# ----------------------------------------------------------------------
def get_raw_dir() -> Path:
    return Path("data/raw")


def get_processed_dir() -> Path:
    return Path("data/processed")


def get_stratified_dir() -> Path:
    return Path("data/stratified")


def get_features_dir() -> Path:
    return Path("data/features")


def get_results_dir() -> Path:
    return Path("data/results")


def get_figures_dir() -> Path:
    return Path("figures")


# ----------------------------------------------------------------------
# Miscellaneous configuration values (place‑holders – real values can be
# overridden by environment variables or a future config file)
# ----------------------------------------------------------------------
def get_motion_threshold() -> float:
    return float(os.getenv("MOTION_THRESHOLD", "0.2"))


def get_texture_threshold() -> float:
    return float(os.getenv("TEXTURE_THRESHOLD", "0.5"))


def get_feature_density_threshold() -> float:
    return float(os.getenv("FEATURE_DENSITY_THRESHOLD", "0.1"))


def get_thresholds() -> dict:
    return {
        "motion": get_motion_threshold(),
        "texture": get_texture_threshold(),
        "feature_density": get_feature_density_threshold(),
    }


def get_memory_limit_gb() -> float:
    """Maximum RAM (in GB) that any phase should attempt to use."""
    return float(os.getenv("MEMORY_LIMIT_GB", "6.0"))


def get_config_summary() -> dict:
    """Return a dictionary summarising the most important config values."""
    return {
        "raw_dir": str(get_raw_dir()),
        "processed_dir": str(get_processed_dir()),
        "stratified_dir": str(get_stratified_dir()),
        "features_dir": str(get_features_dir()),
        "results_dir": str(get_results_dir()),
        "figures_dir": str(get_figures_dir()),
        "thresholds": get_thresholds(),
        "memory_limit_gb": get_memory_limit_gb(),
    }


# ----------------------------------------------------------------------
# Directory creation utility – tolerant to a wide range of call signatures
# ----------------------------------------------------------------------
def _to_path_list(paths: Union[Path, Iterable[Path], None]) -> List[Path]:
    """
    Normalise ``paths`` to a list of ``Path`` objects.

    * ``None`` → empty list
    * ``Path`` → [Path]
    * ``Iterable[Path]`` → list(Iterable)
    * any other type → ignored
    """
    if paths is None:
        return []
    if isinstance(paths, Path):
        return [paths]
    if isinstance(paths, (list, tuple, set)):
        # Filter out non‑Path entries just in case
        return [p for p in paths if isinstance(p, Path)]
    # Fallback – try to iterate, otherwise ignore
    try:
        return [p for p in paths if isinstance(p, Path)]
    except TypeError:
        return []


def ensure_directories(*paths: Union[Path, Iterable[Path], None]) -> None:
    """
    Ensure that a set of directories exists.

    If called with no arguments, the function creates the standard
    project directories (raw, processed, stratified, features, results,
    figures).  When one or more ``Path`` objects (or iterables of ``Path``)
    are supplied, each of those directories is created individually.

    The function is deliberately forgiving – passing ``None`` or a
    non‑Path object does not raise an exception.
    """
    # Standard layout – used when the caller supplies no explicit paths
    if not paths:
        std_dirs = [
            get_raw_dir(),
            get_processed_dir(),
            get_stratified_dir(),
            get_features_dir(),
            get_results_dir(),
            get_figures_dir(),
        ]
        for d in std_dirs:
            d.mkdir(parents=True, exist_ok=True)
        return

    # Caller supplied explicit directories – normalise and create them
    for p in paths:
        for dir_path in _to_path_list(p):
            dir_path.mkdir(parents=True, exist_ok=True)

# The public API of this module is defined by ``__all__`` – this helps
# static analysis tools and prevents accidental export of helper symbols.
__all__ = [
    "get_raw_dir",
    "get_processed_dir",
    "get_stratified_dir",
    "get_features_dir",
    "get_results_dir",
    "get_figures_dir",
    "get_motion_threshold",
    "get_texture_threshold",
    "get_feature_density_threshold",
    "get_thresholds",
    "get_memory_limit_gb",
    "get_config_summary",
    "ensure_directories",
]