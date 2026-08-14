"""
Configuration module for the EEG analysis pipeline.
Defines constants, paths, and utility functions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Global Seed
_GLOBAL_SEED = 42

def set_global_seed(seed: int = 42):
    """Set global seeds for reproducibility."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: sklearn seed setting is usually done per estimator or via global seed if available

def get_seed() -> int:
    """Get the current global seed."""
    return _GLOBAL_SEED

# Path Configuration
# This dictionary maps logical names to relative paths from PROJECT_ROOT
PATH_CONFIG = {
    "data_raw": "data/raw",
    "data_interim": "data/interim",
    "data_processed": "data/processed",
    "cleaned_eeg_final": "data/interim/cleaned_eeg_final",
    "cleaned_eeg_raw": "data/interim/cleaned_eeg_raw",
    "eeg_psd": "data/interim/eeg_psd.csv",
    "behavioral_metrics": "data/interim/behavioral_metrics.csv",
    "features": "data/processed/features.csv",
    "model_results": "data/processed/model_results.json",
    "correlations": "data/processed/correlations.csv",
    "robustness_report": "data/processed/robustness_report.csv",
    "sensitivity_plot": "data/processed/sensitivity_plot.png",
    "verification_log": "data/processed/verification_log.json",
    "final_report": "data/processed/final_report.md",
    "split_indices": "data/interim/split_indices.json",
    "joined_metadata": "data/interim/joined_metadata.csv",
    "exclusion_log": "data/interim/exclusion_log.csv",
    "behavioral_exclusion_log": "data/interim/behavioral_exclusion_log.csv",
    "non_linear_comparison": "data/processed/non_linear_comparison.json",
    "raw_data": "data/raw", # Alias for data_raw
    "processed_data": "data/processed", # Alias for data_processed
    "interim": "data/interim",
    "processed": "data/processed",
}

def get_path(name: str, *args, **kwargs) -> str:
    """
    Get a path from the configuration.
    
    Handles multiple calling conventions:
    1. get_path("data_raw") -> returns "data/raw"
    2. get_path("processed", "features.csv") -> returns "data/processed/features.csv"
    3. get_path(base_dir, "data/processed/features.csv") -> if base_dir is not a known key, treat as prefix?
       Actually, looking at the error: get_path(base_dir, "data/processed/model_results.json")
       If base_dir is a string like "data", and the second arg is the full path?
       Or maybe base_dir is ignored and the second arg is the key?
       
       Let's support:
       - get_path(key) -> PATH_CONFIG[key]
       - get_path(key, sub_path) -> PATH_CONFIG[key] / sub_path
       - get_path(full_path_string) -> full_path_string (if not in config, return as is or join with root?)
       
       The error trace shows: get_path(base_dir, "data/processed/model_results.json")
       If base_dir is "data", and "data" is not in PATH_CONFIG, we need to handle it.
       
       Let's make it flexible:
       If the first arg is in PATH_CONFIG, use it as base.
       If the first arg is a path string and the second is a path string, join them.
       If only one arg and it's in PATH_CONFIG, return it.
       If only one arg and not in PATH_CONFIG, return it (assume it's a full path).
    """
    # Handle the case where the first argument is a base_dir that might be a key or a path
    first_arg = name
    second_arg = args[0] if args else None
    
    # Case 1: get_path("key")
    if second_arg is None:
        if first_arg in PATH_CONFIG:
            return str(PROJECT_ROOT / PATH_CONFIG[first_arg])
        else:
            # Assume it's a relative path from root
            return str(PROJECT_ROOT / first_arg)
    
    # Case 2: get_path("key", "subpath")
    if first_arg in PATH_CONFIG:
        base = PROJECT_ROOT / PATH_CONFIG[first_arg]
        return str(base / second_arg)
    
    # Case 3: get_path("some/path", "another/path") -> join them
    # This handles calls like get_path(base_dir, "data/processed/...") where base_dir might be "data"
    # If "data" is not in PATH_CONFIG, we treat first_arg as a path component.
    # But wait, "data" is not in PATH_CONFIG. "data_raw" is.
    # The call get_path(base_dir, "data/processed/model_results.json") suggests base_dir might be "data".
    # If base_dir is "data", and we join "data" + "data/processed/...", we get "data/data/processed/...".
    # Maybe the caller intends to pass the full path in the second arg?
    # Let's check the error: get_path(base_dir, "data/processed/model_results.json")
    # If base_dir is "data", maybe they want "data/processed/model_results.json".
    # If the second arg is an absolute-like path (starts with data/), maybe we ignore base_dir?
    # Or maybe base_dir is "data" and we want to append "processed/..."?
    
    # Let's try to be robust:
    # If second_arg starts with 'data/', treat it as a relative path from root?
    if second_arg.startswith("data/"):
        return str(PROJECT_ROOT / second_arg)
    
    # Otherwise, join first_arg and second_arg
    return str(PROJECT_ROOT / first_arg / second_arg)

def ensure_dirs(*paths: Union[str, List[str], Path]) -> Path:
    """
    Create directories for the given paths.
    Handles multiple calling conventions:
    1. ensure_dirs() -> does nothing
    2. ensure_dirs("path/to/dir") -> creates path/to/dir
    3. ensure_dirs(["path1", "path2"]) -> creates both
    4. ensure_dirs(Path("path")) -> creates path
    """
    if not paths:
        return Path(".")
    
    # Flatten if a list is passed as the first argument
    path_list = []
    for p in paths:
        if isinstance(p, list):
            path_list.extend(p)
        else:
            path_list.append(p)
    
    for p in path_list:
        if isinstance(p, str):
            # Check if it's a relative path or absolute
            if os.path.isabs(p):
                target = Path(p)
            else:
                # Assume relative to project root? Or current dir?
                # Most calls seem to be relative paths like "data/raw"
                target = PROJECT_ROOT / p
        elif isinstance(p, Path):
            target = p
        else:
            continue
        
        target.mkdir(parents=True, exist_ok=True)
    
    # Return the last path created (or first if only one) for convenience
    if path_list:
        first = path_list[0]
        if isinstance(first, list): first = first[0]
        if isinstance(first, str):
            if os.path.isabs(first): return Path(first)
            return PROJECT_ROOT / first
        return first
    return Path(".")

# Filter Parameters
def get_filter_params() -> Dict[str, Any]:
    return {
        "l_freq": 1.0,
        "h_freq": 40.0,
        "notch_freq": 50.0, # or 60.0 depending on region
    }

# ICA Parameters
def get_ica_params() -> Dict[str, Any]:
    return {
        "n_components": 0.95,
        "method": "fastica",
        "random_state": get_seed()
    }

# Exclusion Parameters
def get_exclusion_params() -> Dict[str, Any]:
    return {
        "max_channel_rejection_ratio": 0.30,
        "min_trials_ratio": 0.70
    }

# Band Frequencies
def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    return {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 45.0)
    }

def get_all_band_names() -> List[str]:
    return list(get_band_freqs().keys())

# Windowing
def get_window_seconds() -> float:
    return 4.0

def get_overlap_seconds() -> float:
    return 2.0

# Cross-Validation
def get_cv_folds() -> int:
    return 5

# Load config from file if exists
def load_config(config_path: Optional[str] = None) -> Dict:
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}