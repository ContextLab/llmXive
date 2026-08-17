"""
Configuration module for the EEG analysis pipeline.
Handles paths, filter parameters, ICA settings, and exclusion rules.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# Global configuration
_CONFIG = {
    "seed": 42,
    "paths": {
        "root": str(Path(__file__).parent.parent),
        "data_raw": "data/raw",
        "data_interim": "data/interim",
        "data_processed": "data/processed",
        "figures": "figures",
        "raw_data": "data/raw", # Alias for compatibility
        "processed_data": "data/processed", # Alias
        "behavioral_metrics": "data/interim/behavioral_metrics.csv", # Specific file path
        "model_results": "data/processed/model_results.json", # Specific file path
    },
    "filter": {
        "l_freq": 1.0,
        "h_freq": 40.0,
        "notch_freqs": [50.0, 60.0]
    },
    "ica": {
        "n_components": 0.99,
        "method": "fastica",
        "random_state": 42
    },
    "exclusion": {
        "max_rejection_ratio": 0.30,
        "min_trials_ratio": 0.70
    },
    "bands": {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 40.0)
    },
    "window_size": 4,
    "epoch_duration": 300,
    "overlap_deferred": True, # Placeholder as per spec
    "cv_folds": 5
}

def load_config() -> Dict[str, Any]:
    return _CONFIG

def set_global_seed(seed: Optional[int] = None):
    if seed is None:
        seed = _CONFIG["seed"]
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> int:
    return _CONFIG["seed"]

def ensure_dirs(*args):
    """
    Create directories if they do not exist.
    Handles multiple call signatures:
    - ensure_dirs() -> returns root data dir
    - ensure_dirs(path) -> creates single path
    - ensure_dirs([path1, path2]) -> creates multiple paths
    - ensure_dirs("processed") -> creates relative path from config
    """
    root = Path(_CONFIG["paths"]["root"])
    
    if not args:
        # Called with no args: ensure base dirs exist
        for path_key in ["data_raw", "data_interim", "data_processed", "figures"]:
            p = root / _CONFIG["paths"][path_key]
            p.mkdir(parents=True, exist_ok=True)
        return root / "data"
    
    for arg in args:
        if isinstance(arg, list):
            for item in arg:
                _make_dir(root, item)
        elif isinstance(arg, str):
            # Check if it's a key or a path
            if arg in _CONFIG["paths"]:
                p = root / _CONFIG["paths"][arg]
            elif os.path.isabs(arg):
                p = Path(arg)
            else:
                # Relative path
                p = root / arg
            _make_dir(root, p)
        elif isinstance(arg, Path):
            _make_dir(root, arg)
        elif isinstance(arg, os.PathLike):
            _make_dir(root, Path(arg))
    
    return None

def _make_dir(root: Path, target: Union[str, Path]):
    if isinstance(target, str):
        target = Path(target)
    if not target.is_absolute():
        target = root / target
    target.mkdir(parents=True, exist_ok=True)

def get_path(*args) -> Path:
    """
    Resolve path based on flexible arguments.
    Signatures:
    - get_path("raw_data") -> Path to raw_data dir
    - get_path("interim", "file.csv") -> Path to interim/file.csv
    - get_path(base_dir, "relative") -> base_dir / relative
    - get_path("data/processed/model_results.json") -> absolute path
    """
    root = Path(_CONFIG["paths"]["root"])
    
    if len(args) == 0:
        return root
    
    # Case 1: get_path(base_dir_str, relative_path_str)
    if len(args) == 2:
        base, rel = args
        if isinstance(base, str) and os.path.isabs(base):
            return Path(base) / rel
        if isinstance(base, Path):
            return base / rel
        # Assume base is a key or relative
        base_path = root / base if not os.path.isabs(base) else Path(base)
        return base_path / rel
    
    # Case 2: get_path(key) or get_path(full_relative_path)
    if len(args) == 1:
        key = args[0]
        if isinstance(key, Path):
            return key
        if isinstance(key, str):
            # Check if it's a config key
            if key in _CONFIG["paths"]:
                return root / _CONFIG["paths"][key]
            # Check if it's an absolute path
            if os.path.isabs(key):
                return Path(key)
            # Assume it's a relative path from root
            return root / key
    
    # Fallback
    return root

def get_filter_params() -> Dict[str, Any]:
    return _CONFIG["filter"]

def get_ica_params() -> Dict[str, Any]:
    return _CONFIG["ica"]

def get_exclusion_params() -> Dict[str, Any]:
    return _CONFIG["exclusion"]

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    return _CONFIG["bands"]

def get_all_band_names() -> List[str]:
    return list(_CONFIG["bands"].keys())

def get_window_seconds() -> int:
    return _CONFIG["window_size"]

def get_overlap_seconds() -> Optional[float]:
    if _CONFIG.get("overlap_deferred"):
        return None # Must be resolved
    return 2.0 # Default fallback if resolved

def get_cv_folds() -> int:
    return _CONFIG["cv_folds"]

def get_min_epoch_duration_minutes() -> int:
    return _CONFIG["epoch_duration"] // 60

def bonferroni_correct(p_value: float, n_tests: int) -> float:
    return p_value * n_tests

# Aliases for compatibility with existing code
def get_raw_data_dir() -> Path:
    return get_path("raw_data")

def get_interim_dir() -> Path:
    return get_path("data_interim")

def get_processed_dir() -> Path:
    return get_path("data_processed")
