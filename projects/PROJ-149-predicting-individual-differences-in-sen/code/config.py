"""
Configuration management for the EEG preprocessing pipeline.
Defines paths, band definitions, ICA params, chunk sizes, and utility functions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# Constants
EPSILON = 1e-9
OVERLAP = 0.5
WINDOW_SIZE = 2.0  # seconds

# Global seed
_GLOBAL_SEED = 42

# Default configuration paths (relative to project root)
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": "data/raw",
        "data_interim": "data/interim",
        "data_processed": "data/processed",
        "figures": "figures",
        "raw_data": "data/raw",  # Alias for compatibility
        "processed": "data/processed",  # Alias for compatibility
        "interim": "data/interim"  # Alias for compatibility
    },
    "filter": {
        "lowcut": 1.0,
        "highcut": 40.0,
        "notch": [50, 60]
    },
    "ica": {
        "n_components": 0.99,
        "method": "fastica"
    },
    "exclusion": {
        "bad_channel_threshold_std": 3.0,
        "max_bad_channel_ratio": 0.30
    },
    "bands": {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 40.0)
    },
    "window": {
        "seconds": 2.0,
        "overlap": 0.5
    },
    "cv": {
        "folds": 5
    }
}

_CONFIG = None

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file or use defaults."""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            _CONFIG = yaml.safe_load(f)
            # Merge with defaults
            for key, value in DEFAULT_CONFIG.items():
                if key not in _CONFIG:
                    _CONFIG[key] = value
    else:
        _CONFIG = DEFAULT_CONFIG

    return _CONFIG

def set_global_seed(seed: int = 42) -> None:
    """Set global random seed for reproducibility."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    np.random.seed(seed)
    random.seed(seed)

def get_seed() -> int:
    """Get the current global seed."""
    return _GLOBAL_SEED

def get_epsilon() -> float:
    """Get the epsilon value for numerical stability."""
    return EPSILON

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency bands."""
    config = load_config()
    return config.get("bands", DEFAULT_CONFIG["bands"])

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(get_band_freqs().keys())

def get_window_seconds() -> float:
    """Get window size in seconds."""
    config = load_config()
    return config.get("window", {}).get("seconds", WINDOW_SIZE)

def get_overlap_seconds() -> float:
    """Get overlap ratio."""
    config = load_config()
    return config.get("window", {}).get("overlap", OVERLAP)

def get_min_epoch_duration_minutes() -> int:
    """Get minimum epoch duration in minutes."""
    return 5

def get_cv_folds() -> int:
    """Get number of CV folds."""
    config = load_config()
    return config.get("cv", {}).get("folds", 5)

def get_filter_params() -> Dict[str, Any]:
    """Get filter parameters."""
    config = load_config()
    return config.get("filter", DEFAULT_CONFIG["filter"])

def get_ica_params() -> Dict[str, Any]:
    """Get ICA parameters."""
    config = load_config()
    return config.get("ica", DEFAULT_CONFIG["ica"])

def get_exclusion_params() -> Dict[str, Any]:
    """Get exclusion parameters."""
    config = load_config()
    return config.get("exclusion", DEFAULT_CONFIG["exclusion"])

def bonferroni_correct(p_values: List[float], n_tests: Optional[int] = None) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    if n_tests is None:
        n_tests = len(p_values)
    return [min(p * n_tests, 1.0) for p in p_values]

def get_path(*args: Union[str, Path]) -> str:
    """
    Get a path from the configuration.
    Flexible signature support:
      - get_path("raw_data") -> returns config path for "raw_data"
      - get_path("data/processed") -> returns absolute path
      - get_path("interim", "preprocessed_eeg") -> joins "data/interim/preprocessed_eeg"
      - get_path(base_dir, "data/processed/file.json") -> joins base_dir + relative path
    """
    config = load_config()
    paths_config = config.get("paths", {})

    # Handle multiple arguments
    if len(args) == 1:
        arg = args[0]
        # Check if it's a known config key
        if isinstance(arg, str) and arg in paths_config:
            base = paths_config[arg]
            return str(Path(base))
        # Otherwise treat as absolute or relative path
        return str(Path(arg))
    else:
        # Multiple args: first is base, rest are subpaths
        base = args[0]
        # Check if base is a config key
        if isinstance(base, str) and base in paths_config:
            base = paths_config[base]
        else:
            base = str(base)

        # Join remaining parts
        subpath = Path(*args[1:])
        return str(Path(base) / subpath)

def ensure_dirs(*args: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Ensure directories exist.
    Flexible signature support:
      - ensure_dirs() -> does nothing
      - ensure_dirs("path/to/dir") -> creates single dir
      - ensure_dirs(["path1", "path2"]) -> creates list of dirs
      - ensure_dirs(Path("path")) -> creates Path object
    """
    if not args:
        return

    paths_to_create = []

    # Handle single list argument
    if len(args) == 1 and isinstance(args[0], list):
        paths_to_create = args[0]
    else:
        paths_to_create = list(args)

    for path in paths_to_create:
        if path is None:
            continue
        # Convert to Path object
        path_obj = Path(path)
        # Create directory if it doesn't exist
        path_obj.mkdir(parents=True, exist_ok=True)


def set_global_seed(seed: int = 42) -> None:
    """Set global random seed for reproducibility."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    np.random.seed(seed)
    random.seed(seed)

def get_seed() -> int:
    """Get the current global seed."""
    return _GLOBAL_SEED

def get_epsilon() -> float:
    """Get the epsilon value for numerical stability."""
    return EPSILON

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency bands."""
    config = load_config()
    return config.get("bands", DEFAULT_CONFIG["bands"])

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(get_band_freqs().keys())

def get_window_seconds() -> float:
    """Get window size in seconds."""
    config = load_config()
    return config.get("window", {}).get("seconds", WINDOW_SIZE)

def get_overlap_seconds() -> float:
    """Get overlap ratio."""
    config = load_config()
    return config.get("window", {}).get("overlap", OVERLAP)

def get_min_epoch_duration_minutes() -> int:
    """Get minimum epoch duration in minutes."""
    return 5

def get_cv_folds() -> int:
    """Get number of CV folds."""
    config = load_config()
    return config.get("cv", {}).get("folds", 5)

def get_filter_params() -> Dict[str, Any]:
    """Get filter parameters."""
    config = load_config()
    return config.get("filter", DEFAULT_CONFIG["filter"])

def get_ica_params() -> Dict[str, Any]:
    """Get ICA parameters."""
    config = load_config()
    return config.get("ica", DEFAULT_CONFIG["ica"])

def get_exclusion_params() -> Dict[str, Any]:
    """Get exclusion parameters."""
    config = load_config()
    return config.get("exclusion", DEFAULT_CONFIG["exclusion"])

def bonferroni_correct(p_values: List[float], n_tests: Optional[int] = None) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    if n_tests is None:
        n_tests = len(p_values)
    return [min(p * n_tests, 1.0) for p in p_values]

def get_path(*args: Union[str, Path]) -> str:
    """
    Get a path from the configuration.
    Flexible signature support:
      - get_path("raw_data") -> returns config path for "raw_data"
      - get_path("data/processed") -> returns absolute path
      - get_path("interim", "preprocessed_eeg") -> joins "data/interim/preprocessed_eeg"
      - get_path(base_dir, "data/processed/file.json") -> joins base_dir + relative path
    """
    config = load_config()
    paths_config = config.get("paths", {})

    # Handle multiple arguments
    if len(args) == 1:
        arg = args[0]
        # Check if it's a known config key
        if isinstance(arg, str) and arg in paths_config:
            base = paths_config[arg]
            return str(Path(base))
        # Otherwise treat as absolute or relative path
        return str(Path(arg))
    else:
        # Multiple args: first is base, rest are subpaths
        base = args[0]
        # Check if base is a config key
        if isinstance(base, str) and base in paths_config:
            base = paths_config[base]
        else:
            base = str(base)

        # Join remaining parts
        subpath = Path(*args[1:])
        return str(Path(base) / subpath)

def ensure_dirs(*args: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Ensure directories exist.
    Flexible signature support:
      - ensure_dirs() -> does nothing
      - ensure_dirs("path/to/dir") -> creates single dir
      - ensure_dirs(["path1", "path2"]) -> creates list of dirs
      - ensure_dirs(Path("path")) -> creates Path object
    """
    if not args:
        return

    paths_to_create = []

    # Handle single list argument
    if len(args) == 1 and isinstance(args[0], list):
        paths_to_create = args[0]
    else:
        paths_to_create = list(args)

    for path in paths_to_create:
        if path is None:
            continue
        # Convert to Path object
        path_obj = Path(path)
        # Create directory if it doesn't exist
        path_obj.mkdir(parents=True, exist_ok=True)
