"""
Configuration constants and utility functions for the EEG analysis pipeline.
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
        "project_root": Path(__file__).parent.parent,
        "data_raw": "data/raw",
        "data_interim": "data/interim",
        "data_processed": "data/processed",
        "figures": "figures",
        "cleaned_eeg_final": "data/interim/cleaned_eeg_final",
        "robustness": "data/interim/robustness",
        # Legacy aliases for backward compatibility
        "raw_data": "data/raw",
        "interim": "data/interim",
        "processed": "data/processed",
        "processed_data": "data/processed",
        "behavioral_metrics": "data/interim/behavioral_metrics.csv",
        "model_results": "data/processed/model_results.json",
    },
    "filter": {
        "low_cut": 1.0,
        "high_cut": 40.0,
        "notch_freqs": [50.0, 60.0],
    },
    "ica": {
        "n_components": 0.99,  # Variance retention
        "random_state": 42,
        "method": "fastica",
    },
    "exclusion": {
        "variance_threshold_std": 3.0,
        "min_trials_ratio": 0.70,
        "rt_min_ms": 100,
        "rt_max_ms": 2000,
    },
    "bands": {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 40.0),
    },
    "window": {
        "size_seconds": 4,
        "epoch_duration_seconds": 300,  # 5 minutes
        "overlap_ratio": 0.5,
    },
    "model": {
        "cv_folds": 5,
        "batch_size": 100,
    },
    "stats": {
        "epsilon": 1e-10,
        "p_value_threshold": 0.05,
    },
}

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from a YAML file or return defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f)
            # Deep merge user config into defaults
            _deep_update(_CONFIG, user_config)
    return _CONFIG

def _deep_update(d: Dict, u: Dict) -> Dict:
    """Recursively update dictionary d with values from u."""
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            _deep_update(d[k], v)
        else:
            d[k] = v
    return d

def set_global_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    _CONFIG["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)
    if "random_state" in _CONFIG.get("ica", {}):
        _CONFIG["ica"]["random_state"] = seed

def get_seed() -> int:
    """Get the current global seed."""
    return _CONFIG.get("seed", 42)

def ensure_dirs(*args) -> Union[Path, List[Path], None]:
    """
    Create directories if they don't exist.
    Accepts multiple calling patterns:
      - ensure_dirs() -> None (no-op)
      - ensure_dirs("relative/path") -> Path
      - ensure_dirs(Path("...")) -> Path
      - ensure_dirs(["path1", "path2"]) -> List[Path]
      - ensure_dirs(path1, path2) -> List[Path]
    """
    if not args:
        return None

    # Normalize inputs to a list of Path objects
    paths_to_create = []
    for arg in args:
        if isinstance(arg, list):
            paths_to_create.extend(arg)
        else:
            paths_to_create.append(arg)

    created_paths = []
    for p in paths_to_create:
        if p is None:
            continue
        # Handle relative paths by joining with project root
        if isinstance(p, str):
            # Check if it looks like a relative key or a full path
            if p in _CONFIG["paths"]:
                base = _CONFIG["paths"]["project_root"]
                rel = _CONFIG["paths"][p]
                full_path = base / rel
            elif p.startswith("data/") or p.startswith("figures/"):
                base = _CONFIG["paths"]["project_root"]
                full_path = base / p
            else:
                # Assume it's a relative path from project root
                base = _CONFIG["paths"]["project_root"]
                full_path = base / p
        elif isinstance(p, Path):
            if not p.is_absolute():
                full_path = _CONFIG["paths"]["project_root"] / p
            else:
                full_path = p
        else:
            continue

        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
        except (OSError, PermissionError) as e:
            # Log error but continue creating others
            print(f"Warning: Could not create directory {full_path}: {e}")

    # Return single Path if only one, else list
    if len(created_paths) == 1:
        return created_paths[0]
    elif len(created_paths) > 1:
        return created_paths
    return None

def get_path(*args) -> Path:
    """
    Resolve a path based on various calling conventions.
    Supports:
      - get_path("key_name") -> Path to predefined key
      - get_path("data/processed") -> Absolute path
      - get_path("base_dir", "relative/path") -> Join base and relative
      - get_path(Path(...)) -> Return as-is or resolve relative to root
    """
    if not args:
        raise ValueError("get_path() requires at least one argument")

    # Case 1: Single string argument - check if it's a key or a path
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, str):
            if arg in _CONFIG["paths"]:
                base = _CONFIG["paths"]["project_root"]
                rel = _CONFIG["paths"][arg]
                return base / rel
            elif arg.startswith("data/") or arg.startswith("figures/"):
                return _CONFIG["paths"]["project_root"] / arg
            else:
                # Assume it's a relative path
                return _CONFIG["paths"]["project_root"] / arg
        elif isinstance(arg, Path):
            if not arg.is_absolute():
                return _CONFIG["paths"]["project_root"] / arg
            return arg
        else:
            raise TypeError(f"Unexpected argument type: {type(arg)}")

    # Case 2: Multiple arguments - treat first as base, rest as relative
    base_arg = args[0]
    if isinstance(base_arg, str) and base_arg in _CONFIG["paths"]:
        base = _CONFIG["paths"]["project_root"] / _CONFIG["paths"][base_arg]
    elif isinstance(base_arg, Path):
        base = base_arg if base_arg.is_absolute() else _CONFIG["paths"]["project_root"] / base_arg
    elif isinstance(base_arg, str):
        # Assume it's a path string
        base = _CONFIG["paths"]["project_root"] / base_arg
    else:
        raise TypeError(f"Unexpected base argument type: {type(base_arg)}")

    # Join remaining arguments
    for rel_part in args[1:]:
        if isinstance(rel_part, Path):
            base = base / rel_part
        elif isinstance(rel_part, str):
            base = base / rel_part
        else:
            raise TypeError(f"Unexpected path part type: {type(rel_part)}")

    return base

def get_filter_params() -> Dict[str, float]:
    """Get filter parameters."""
    return _CONFIG["filter"]

def get_ica_params() -> Dict[str, Any]:
    """Get ICA parameters."""
    return _CONFIG["ica"]

def get_exclusion_params() -> Dict[str, Any]:
    """Get exclusion criteria parameters."""
    return _CONFIG["exclusion"]

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency bands."""
    return _CONFIG["bands"]

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(_CONFIG["bands"].keys())

def get_window_seconds() -> float:
    """Get window size in seconds."""
    return _CONFIG["window"]["size_seconds"]

def get_overlap_seconds() -> float:
    """Get overlap in seconds."""
    return _CONFIG["window"]["size_seconds"] * _CONFIG["window"]["overlap_ratio"]

def get_cv_folds() -> int:
    """Get number of CV folds."""
    return _CONFIG["model"]["cv_folds"]

def get_min_epoch_duration_minutes() -> int:
    """Get minimum epoch duration in minutes."""
    return _CONFIG["window"]["epoch_duration_seconds"] // 60

def bonferroni_correct(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    alpha = _CONFIG["stats"]["p_value_threshold"]
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected
