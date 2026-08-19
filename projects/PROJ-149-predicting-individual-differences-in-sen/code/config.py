"""
Configuration module for the EEG analysis pipeline.
Defines constants, paths, and helper functions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": "data/raw",
        "data_interim": "data/interim",
        "data_processed": "data/processed",
        "figures": "figures",
        "code": "code",
        "specs": "specs"
    },
    "filter_params": {
        "low_cutoff": 1.0,
        "high_cutoff": 40.0,
        "notch_freq": 50.0,  # 50Hz or 60Hz depending on region
        "filter_order": 4
    },
    "ica_params": {
        "n_components": 0.99,
        "method": "fastica"
    },
    "exclusion_params": {
        "max_channel_rejection_ratio": 0.30
    },
    "band_definitions": {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 45.0)
    },
    "window_params": {
        "epoch_duration_minutes": 5,
        "window_seconds": 4,
        "overlap": 0.5  # Default 0.5 if [deferred] and justified
    },
    "modeling_params": {
        "cv_folds": 5,
        "random_state": 42
    },
    "epsilon": 1e-9,
    "overlap_deferred_justified": False  # Set to True if plan.md justification found
}

_config = DEFAULT_CONFIG.copy()

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from YAML file or return defaults."""
    global _config
    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                user_config = yaml.safe_load(f)
                _config.update(user_config)
    return _config

def set_global_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    """Get the current random seed."""
    return _config.get("modeling_params", {}).get("random_state", 42)

def ensure_dirs(*args) -> Any:
    """
    Ensure directories exist.
    Handles multiple call signatures to be tolerant of all callers:
    - ensure_dirs() -> returns None (no-op)
    - ensure_dirs(path_str) -> returns Path
    - ensure_dirs(path_obj) -> returns Path
    - ensure_dirs([path1, path2]) -> returns list of Paths
    """
    if not args:
        return None
    
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, list):
            results = []
            for item in arg:
                if isinstance(item, str):
                    p = Path(item)
                elif isinstance(item, Path):
                    p = item
                else:
                    p = Path(str(item))
                p.mkdir(parents=True, exist_ok=True)
                results.append(p)
            return results
        elif isinstance(arg, str):
            p = Path(arg)
            p.mkdir(parents=True, exist_ok=True)
            return p
        elif isinstance(arg, Path):
            arg.mkdir(parents=True, exist_ok=True)
            return arg
        else:
            # Try to convert to Path
            p = Path(str(arg))
            p.mkdir(parents=True, exist_ok=True)
            return p
    else:
        # Multiple arguments: treat as list of paths
        results = []
        for arg in args:
            if isinstance(arg, str):
                p = Path(arg)
            elif isinstance(arg, Path):
                p = arg
            else:
                p = Path(str(arg))
            p.mkdir(parents=True, exist_ok=True)
            results.append(p)
        return results

def get_path(*args) -> Path:
    """
    Get a path relative to project root or specific base.
    Handles multiple call signatures:
    - get_path("data_raw") -> Path to data/raw
    - get_path("processed", "features.csv") -> Path to data/processed/features.csv
    - get_path(base_dir, "relative/path") -> Path(base_dir) / relative/path
    """
    if not args:
        return PROJECT_ROOT
    
    first_arg = args[0]
    
    # Case 1: get_path("key_name") where key_name is in DEFAULT_CONFIG["paths"]
    if len(args) == 1 and isinstance(first_arg, str):
        key = first_arg
        if key in _config.get("paths", {}):
            return PROJECT_ROOT / _config["paths"][key]
        elif key.startswith("data/"):
            # Direct path
            return PROJECT_ROOT / key
        else:
            # Assume it's a relative path
            return PROJECT_ROOT / key
    
    # Case 2: get_path(base_dir, relative_path)
    if len(args) >= 2:
        base = args[0]
        relative = args[1]
        if isinstance(base, str):
            if base in _config.get("paths", {}):
                base_path = PROJECT_ROOT / _config["paths"][base]
            else:
                base_path = Path(base)
        elif isinstance(base, Path):
            base_path = base
        else:
            base_path = Path(str(base))
        
        if isinstance(relative, str):
            return base_path / relative
        elif isinstance(relative, Path):
            return base_path / relative
        else:
            return base_path / str(relative)
    
    # Case 3: Single Path object or string path
    if isinstance(first_arg, Path):
        return first_arg
    elif isinstance(first_arg, str):
        return Path(first_arg)
    
    return PROJECT_ROOT

def get_filter_params() -> Dict:
    """Get filter parameters."""
    return _config.get("filter_params", {})

def get_ica_params() -> Dict:
    """Get ICA parameters."""
    return _config.get("ica_params", {})

def get_exclusion_params() -> Dict:
    """Get exclusion parameters."""
    return _config.get("exclusion_params", {})

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get band frequency definitions."""
    return _config.get("band_definitions", {})

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(get_band_freqs().keys())

def get_window_seconds() -> float:
    """Get window duration in seconds."""
    return _config.get("window_params", {}).get("window_seconds", 4.0)

def get_overlap_seconds() -> float:
    """Get overlap in seconds (calculated from ratio)."""
    window = get_window_seconds()
    ratio = _config.get("window_params", {}).get("overlap", 0.5)
    return window * ratio

def get_cv_folds() -> int:
    """Get number of CV folds."""
    return _config.get("modeling_params", {}).get("cv_folds", 5)

def get_min_epoch_duration_minutes() -> float:
    """Get minimum epoch duration in minutes."""
    return _config.get("window_params", {}).get("epoch_duration_minutes", 5.0)

def bonferroni_correct(p_values: List[float], n_tests: Optional[int] = None) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    if n_tests is None:
        n_tests = len(p_values)
    if n_tests == 0:
        return []
    alpha = 0.05
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

# Initialize config on import
load_config()