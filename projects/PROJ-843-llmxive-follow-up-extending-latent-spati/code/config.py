"""
Configuration management for llmXive pipeline.

Defines paths, thresholds, and utility functions for directory management.
"""
import os
from pathlib import Path
from typing import Iterable, Union, Any, List, Optional, Dict

# Project root (relative to current working directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Directory structure
DIRS = {
    "raw": PROJECT_ROOT / "data" / "raw",
    "processed": PROJECT_ROOT / "data" / "processed",
    "stratified": PROJECT_ROOT / "data" / "stratified",
    "features": PROJECT_ROOT / "data" / "features",
    "results": PROJECT_ROOT / "data" / "results",
    "figures": PROJECT_ROOT / "figures",
}

# RANSAC threshold default
RANSAC_THRESHOLD = 0.05

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_raw_dir() -> Path:
    """Return the raw data directory."""
    return DIRS["raw"]

def get_processed_dir() -> Path:
    """Return the processed data directory."""
    return DIRS["processed"]

def get_stratified_dir() -> Path:
    """Return the stratified data directory."""
    return DIRS["stratified"]

def get_features_dir() -> Path:
    """Return the features directory."""
    return DIRS["features"]

def get_results_dir() -> Path:
    """Return the results directory."""
    return DIRS["results"]

def get_figures_dir() -> Path:
    """Return the figures directory."""
    return DIRS["figures"]

def get_ransac_threshold() -> float:
    """Return the default RANSAC threshold."""
    return RANSAC_THRESHOLD

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "directories": {k: str(v) for k, v in DIRS.items()},
        "ransac_threshold": RANSAC_THRESHOLD,
    }

def ensure_directories(*paths: Union[Path, str, List[Union[Path, str]], Iterable[Union[Path, str]]]) -> None:
    """
    Ensure that the given paths exist as directories.
    
    This function is tolerant of various input shapes:
    - Single Path or str
    - List of Paths/strs
    - Iterable of Paths/strs
    - Mixed arguments
    
    Does not raise on empty inputs or None.
    """
    # Normalize inputs into a flat list of Path objects
    to_create: List[Path] = []
    
    for arg in paths:
        if arg is None:
            continue
        if isinstance(arg, (list, tuple, set)):
            to_create.extend(arg)
        elif isinstance(arg, Path):
            to_create.append(arg)
        elif isinstance(arg, str):
            to_create.append(Path(arg))
        else:
            # Try to iterate if it's an iterable
            try:
                to_create.extend(arg)
            except TypeError:
                # If it's not iterable, skip
                continue
    
    # Create directories
    for path in to_create:
        if path is None:
            continue
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Log but don't fail for individual directory creation errors
            # to allow the pipeline to continue if possible
            pass

# Alias for backward compatibility
create_directories = ensure_directories
