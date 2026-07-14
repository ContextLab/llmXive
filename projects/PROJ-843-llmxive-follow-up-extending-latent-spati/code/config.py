"""
Configuration module for the llmXive follow‑up project.

This module defines standard directory paths, threshold and memory
configuration getters, and a flexible ``ensure_directories`` helper that
can be called with zero or many arguments in a variety of forms
(single Path, iterable of Paths, or multiple positional Path arguments).
"""

import os
from pathlib import Path
from typing import Iterable, List, Union, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
_RAW_DIR = PROJECT_ROOT / "data" / "raw"
_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
_STRATIFIED_DIR = PROJECT_ROOT / "data" / "stratified"
_FEATURES_DIR = PROJECT_ROOT / "data" / "features"
_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Configuration State
_RANSAC_THRESHOLD = 0.05
_MAX_RAM_MB = 8000
_MAX_WALL_TIME_SECONDS = 300

def get_raw_dir() -> Path:
    return _RAW_DIR

def get_processed_dir() -> Path:
    return _PROCESSED_DIR

def get_stratified_dir() -> Path:
    return _STRATIFIED_DIR

def get_features_dir() -> Path:
    return _FEATURES_DIR

def get_results_dir() -> Path:
    return _RESULTS_DIR

def get_ransac_threshold() -> float:
    return _RANSAC_THRESHOLD

def set_ransac_threshold(value: float) -> None:
    global _RANSAC_THRESHOLD
    _RANSAC_THRESHOLD = value

def get_max_ram_mb() -> int:
    return _MAX_RAM_MB

def set_max_ram_mb(value: int) -> None:
    global _MAX_RAM_MB
    _MAX_RAM_MB = value

def get_max_wall_time_seconds() -> int:
    return _MAX_WALL_TIME_SECONDS

def set_max_wall_time_seconds(value: int) -> None:
    global _MAX_WALL_TIME_SECONDS
    _MAX_WALL_TIME_SECONDS = value

def ensure_directories(*dirs: Union[Path, List[Path], Iterable[Path], None]) -> None:
    """
    Robust directory creation accepting various input signatures.
    Compatible with all existing call sites in the project.
    Handles:
      - No args: creates all default directories
      - Single Path: creates that directory
      - List[Path] or Iterable[Path]: creates each
      - Mixed args: processes all valid Path-like objects
    """
    paths_to_create = []

    if not dirs:
        # No arguments: create all default directories
        paths_to_create = [_RAW_DIR, _PROCESSED_DIR, _STRATIFIED_DIR, _FEATURES_DIR, _RESULTS_DIR]
    else:
        for arg in dirs:
            if arg is None:
                continue
            elif isinstance(arg, Path):
                paths_to_create.append(arg)
            elif isinstance(arg, list):
                paths_to_create.extend([p for p in arg if isinstance(p, Path)])
            elif hasattr(arg, '__iter__') and not isinstance(arg, str):
                # Handle generic iterables (sets, tuples, generators)
                paths_to_create.extend([p for p in arg if isinstance(p, Path)])
            else:
                # Fallback for unexpected types, try to convert or ignore
                try:
                    paths_to_create.append(Path(arg))
                except Exception:
                    pass

    for p in paths_to_create:
        if p is not None:
            p.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    return {
        "raw_dir": str(_RAW_DIR),
        "processed_dir": str(_PROCESSED_DIR),
        "stratified_dir": str(_STRATIFIED_DIR),
        "features_dir": str(_FEATURES_DIR),
        "results_dir": str(_RESULTS_DIR),
        "ransac_threshold": _RANSAC_THRESHOLD,
        "max_ram_mb": _MAX_RAM_MB,
        "max_wall_time_seconds": _MAX_WALL_TIME_SECONDS
    }