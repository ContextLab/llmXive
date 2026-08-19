"""
Configuration module for the EEG analysis pipeline.
Defines paths, parameters, and utility functions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# ---------------------------------------------------------------------------
# Global Config State
# ---------------------------------------------------------------------------
_CONFIG = {}
_SEED = 42

def load_config(config_path: Optional[str] = None):
    """Load configuration from YAML file."""
    global _CONFIG
    if config_path is None:
        # Default path relative to project root
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            _CONFIG = yaml.safe_load(f)
    else:
        # Default configuration if file missing
        _CONFIG = {
            "paths": {
                "data_raw": "data/raw",
                "data_interim": "data/interim",
                "data_processed": "data/processed",
                "figures": "figures",
                "cleaned_eeg_final": "data/interim/cleaned_eeg_final",
                "exclusion_log": "data/interim/exclusion_log.csv",
                "behavioral_metrics": "data/interim/behavioral_metrics.csv",
                "features_clr": "data/processed/features_clr.csv",
                "model_results": "data/processed/model_results.json",
                "split_indices": "data/interim/split_indices.json",
                "correlations": "data/processed/correlations.csv",
                "robustness_report": "data/processed/robustness_report.csv",
                "sensitivity_plot": "data/processed/sensitivity_plot.png",
                "verification_log": "data/processed/verification_log.json",
                "final_report": "data/processed/final_report.md",
                "joined_metadata": "data/interim/joined_metadata.csv",
                "feasibility_report": "data/processed/feasibility_report.md",
                "feasibility_exclusion_log": "data/interim/feasibility_exclusion_log.csv",
                "detected_tasks_log": "data/interim/detected_tasks.log",
                "raw_data": "data/raw",
                "processed_data": "data/interim",
                "behavioral": "data/interim",
                "model": "data/processed",
                "interim": "data/interim",
                "processed": "data/processed"
            },
            "filter": {
                "lowcut": 1.0,
                "highcut": 40.0,
                "notch": [50, 60]
            },
            "ica": {
                "method": "fastica",
                "n_components": 0.99,
                "random_state": 42
            },
            "exclusion": {
                "max_bad_channel_ratio": 0.30,
                "bad_channel_threshold_std": 3.0
            },
            "bands": {
                "delta": [1, 4],
                "theta": [4, 8],
                "alpha": [8, 13],
                "low_beta": [13, 20],
                "high_beta": [20, 30],
                "gamma": [30, 45]
            },
            "psd": {
                "window_seconds": 4.0,
                "overlap_seconds": 2.0,
                "min_epoch_duration_minutes": 5.0
            },
            "modeling": {
                "cv_folds": 5,
                "test_size": 0.2
            },
            "epsilon": 1e-9,
            "seed": 42
        }

def set_global_seed(seed: int):
    """Set global random seed."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    return _SEED

def get_epsilon() -> float:
    return _CONFIG.get("epsilon", 1e-9)

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    return _CONFIG.get("bands", {})

def get_all_band_names() -> List[str]:
    return list(get_band_freqs().keys())

def get_window_seconds() -> float:
    return _CONFIG.get("psd", {}).get("window_seconds", 4.0)

def get_overlap_seconds() -> float:
    val = _CONFIG.get("psd", {}).get("overlap_seconds")
    if val is None:
        raise ValueError(
            "OVERLAP not set in config.py. Spec is [deferred]. "
            "Please set OVERLAP or amend spec."
        )
    return val

def get_min_epoch_duration_minutes() -> float:
    return _CONFIG.get("psd", {}).get("min_epoch_duration_minutes", 5.0)

def get_cv_folds() -> int:
    return _CONFIG.get("modeling", {}).get("cv_folds", 5)

def get_filter_params() -> Dict[str, Any]:
    return _CONFIG.get("filter", {})

def get_ica_params() -> Dict[str, Any]:
    return _CONFIG.get("ica", {})

def get_exclusion_params() -> Dict[str, Any]:
    return _CONFIG.get("exclusion", {})

def bonferroni_correct(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction."""
    return [min(p * n_tests, 1.0) for p in p_values]

# ---------------------------------------------------------------------------
# Path Utilities (Flexible Contract)
# ---------------------------------------------------------------------------

def get_path(*args: Any) -> Path:
    """
    Flexible path resolver.
    Supports:
      1. get_path("key_name") -> looks up in paths dict
      2. get_path("key_name", "subpath") -> looks up key, appends subpath
      3. get_path("absolute/path") -> returns as Path
      4. get_path(Path_obj) -> returns Path_obj
    """
    if not args:
        raise ValueError("get_path requires at least one argument")

    # If the first arg is a Path object, return it directly
    if isinstance(args[0], Path):
        return args[0]

    first_arg = str(args[0])

    # Check if it's a known key in the paths config
    paths_config = _CONFIG.get("paths", {})

    if first_arg in paths_config:
        base = paths_config[first_arg]
        if len(args) > 1:
            # Append remaining args
            return Path(base) / "/".join(str(a) for a in args[1:])
        return Path(base)

    # If it looks like an absolute or relative path string, treat as path
    if os.path.isabs(first_arg) or first_arg.startswith("./") or first_arg.startswith("../"):
        if len(args) > 1:
            return Path(first_arg) / "/".join(str(a) for a in args[1:])
        return Path(first_arg)

    # Fallback: treat the whole thing as a relative path
    return Path("/".join(str(a) for a in args))

def ensure_dirs(*args: Any) -> Path:
    """
    Flexible directory creator.
    Supports:
      1. ensure_dirs() -> returns project root
      2. ensure_dirs("path_string") -> ensures path_string exists
      3. ensure_dirs(Path_obj) -> ensures Path_obj exists
      4. ensure_dirs([list_of_paths]) -> ensures all exist
      5. ensure_dirs("key", "subpath") -> resolves key, ensures path
    """
    if not args:
        # Default to project root
        p = Path(__file__).parent.parent
        p.mkdir(exist_ok=True)
        return p

    # Handle list input
    if isinstance(args[0], (list, tuple)):
        for item in args[0]:
            ensure_dirs(item)
        return Path(args[0][0]) if args[0] else Path(".")

    # Handle single Path object
    if isinstance(args[0], Path):
        args[0].mkdir(parents=True, exist_ok=True)
        return args[0]

    # Handle string key or path
    first = str(args[0])
    target_path = get_path(*args)
    target_path.mkdir(parents=True, exist_ok=True)
    return target_path

# Initialize config on import
load_config()
