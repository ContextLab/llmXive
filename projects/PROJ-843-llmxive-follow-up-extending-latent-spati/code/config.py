"""
Configuration module for the llmXive follow‑up project.

This module defines standard directory paths, threshold and memory
configuration getters, and a flexible ``ensure_directories`` helper that
can be called with zero or many arguments in a variety of forms
(single Path, iterable of Paths, or multiple positional Path arguments).
"""

import os
from pathlib import Path
from typing import Iterable, List, Union

# ----------------------------------------------------------------------
# Project root – assumed to be the parent of the ``code`` directory.
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Directory getters
# ----------------------------------------------------------------------
def get_raw_dir() -> Path:
    """Directory for raw downloaded data."""
    return PROJECT_ROOT / "data" / "raw"

def get_processed_dir() -> Path:
    """Directory for processed intermediate data."""
    return PROJECT_ROOT / "data" / "processed"

def get_stratified_dir() -> Path:
    """Directory for stratified dataset splits."""
    return PROJECT_ROOT / "data" / "stratified"

def get_features_dir() -> Path:
    """Directory for extracted visual features."""
    return PROJECT_ROOT / "data" / "features"

def get_results_dir() -> Path:
    """Directory for final results and metrics."""
    return PROJECT_ROOT / "data" / "results"

# ----------------------------------------------------------------------
# Thresholds / limits (placeholder values – real values can be overridden
# by environment variables or downstream configuration files)
# ----------------------------------------------------------------------
def get_threshold(name: str) -> float:
    """Return a numeric threshold by name; defaults to ``1.0``."""
    # In a full implementation these would be looked up from a config file.
    return float(os.getenv(f"THRESHOLD_{name.upper()}", "1.0"))

def get_all_thresholds() -> dict:
    """Return a dictionary of all known thresholds."""
    # Example static thresholds – can be expanded as needed.
    return {
        "optical_flow": get_threshold("optical_flow"),
        "texture_entropy": get_threshold("texture_entropy"),
        "ransac_inlier_ratio": get_threshold("ransac_inlier_ratio"),
    }

# ----------------------------------------------------------------------
# Memory limits
# ----------------------------------------------------------------------
def get_memory_limit_gb() -> int:
    """Maximum RAM (in GB) that the pipeline may use."""
    return int(os.getenv("MEMORY_LIMIT_GB", "8"))

def get_memory_limit_bytes() -> int:
    """Maximum RAM (in bytes)."""
    return get_memory_limit_gb() * 1024 ** 3

# ----------------------------------------------------------------------
# Misc helpers
# ----------------------------------------------------------------------
def get_config_summary() -> dict:
    """Return a compact summary of the current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "raw_dir": str(get_raw_dir()),
        "processed_dir": str(get_processed_dir()),
        "stratified_dir": str(get_stratified_dir()),
        "features_dir": str(get_features_dir()),
        "results_dir": str(get_results_dir()),
        "memory_limit_gb": get_memory_limit_gb(),
        "thresholds": get_all_thresholds(),
    }

# ----------------------------------------------------------------------
# Directory creation helper
# ----------------------------------------------------------------------
def ensure_directories(*paths: Union[Path, Iterable[Path]]) -> None:
    """
    Create one or more directories if they do not already exist.

    This function is deliberately permissive – it accepts:
      * No arguments → creates the standard project directories.
      * A single ``Path``.
      * Multiple ``Path`` objects as positional arguments.
      * An iterable (list/tuple/set) of ``Path`` objects.
      * Mixed positional and iterable arguments.

    Example usages that must all succeed:
        ensure_directories()
        ensure_directories(get_raw_dir())
        ensure_directories([get_raw_dir(), get_results_dir()])
        ensure_directories(get_raw_dir(), get_results_dir())
        ensure_directories(get_raw_dir(), [get_results_dir(), get_features_dir()])
    """
    # If nothing was passed, create the canonical set of directories.
    if not paths:
        dirs: List[Path] = [
            get_raw_dir(),
            get_processed_dir(),
            get_stratified_dir(),
            get_features_dir(),
            get_results_dir(),
        ]
    else:
        # Flatten any iterables while preserving Path objects.
        dirs: List[Path] = []
        for p in paths:
            if isinstance(p, (list, tuple, set)):
                dirs.extend([Path(item) for item in p])
            else:
                dirs.append(Path(p))

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# End of config.py