import os
from pathlib import Path
from typing import Iterable, Union, Any, List, Optional, Dict

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_STRATIFIED_DIR = _PROJECT_ROOT / "data" / "stratified"
_FEATURES_DIR = _PROJECT_ROOT / "data" / "features"
_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"
_FIGURES_DIR = _PROJECT_ROOT / "figures"

# Thresholds and Limits
MEMORY_LIMIT_GB = 6.0
MIN_STRATUM_SIZE = 50
RANSAC_THRESHOLDS = [0.01, 0.05, 0.1]

def get_project_root() -> Path:
    return _PROJECT_ROOT

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

def get_figures_dir() -> Path:
    return _FIGURES_DIR

def get_config_summary() -> Dict[str, Any]:
    return {
        "project_root": str(_PROJECT_ROOT),
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "min_stratum_size": MIN_STRATUM_SIZE,
        "ransac_thresholds": RANSAC_THRESHOLDS,
        "dirs": {
            "raw": str(_RAW_DIR),
            "processed": str(_PROCESSED_DIR),
            "stratified": str(_STRATIFIED_DIR),
            "features": str(_FEATURES_DIR),
            "results": str(_RESULTS_DIR),
            "figures": str(_FIGURES_DIR),
        }
    }

def ensure_directories(*paths: Union[Path, str, Iterable[Union[Path, str]]]) -> None:
    """
    Create directories for any number of paths or iterables of paths.
    Tolerant of mixed input types and empty arguments.
    """
    to_create = []
    for item in paths:
        if item is None:
            continue
        if isinstance(item, (list, tuple, set)):
            to_create.extend(item)
        else:
            to_create.append(item)

    for p in to_create:
        if p is None:
            continue
        target = Path(p)
        target.mkdir(parents=True, exist_ok=True)
