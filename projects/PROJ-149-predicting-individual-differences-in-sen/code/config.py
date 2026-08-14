"""
Configuration constants and utility functions for the EEG Sensory Processing Speed project.
Handles paths, filter parameters, seeds, and band definitions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union

# Global seed state
_SEED = 42

def set_global_seed(seed: int = 42) -> None:
    """Set global seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow
        tensorflow.random.set_seed(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """Get current global seed."""
    return _SEED

# Path definitions
_PATHS = {
    "root": Path(__file__).resolve().parent.parent,
    "code": Path(__file__).resolve().parent,
    "data": Path(__file__).resolve().parent.parent / "data",
    "data_raw": Path(__file__).resolve().parent.parent / "data" / "raw",
    "data_interim": Path(__file__).resolve().parent.parent / "data" / "interim",
    "data_processed": Path(__file__).resolve().parent.parent / "data" / "processed",
    "figures": Path(__file__).resolve().parent.parent / "figures",
    "cleaned_eeg_raw": Path(__file__).resolve().parent.parent / "data" / "interim" / "cleaned_eeg_raw",
    "cleaned_eeg_final": Path(__file__).resolve().parent.parent / "data" / "interim" / "cleaned_eeg_final",
    "robustness": Path(__file__).resolve().parent.parent / "data" / "interim" / "robustness",
}

def ensure_dirs(*args) -> None:
    """
    Create directories if they do not exist.
    Accepts:
      - No arguments: creates default data dirs
      - Single string path: creates that path
      - Single Path object: creates that path
      - List of strings/Paths: creates all
      - Multiple string/Path arguments: creates all
    """
    paths_to_create = []

    if not args:
        # Default behavior: create all standard data directories
        paths_to_create = list(_PATHS.values())
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, list):
            paths_to_create = arg
        elif isinstance(arg, (str, Path)):
            paths_to_create = [Path(arg)]
        else:
            # If it's something else (e.g., a dict), ignore or handle gracefully
            return
    else:
        # Multiple arguments
        paths_to_create = [Path(str(a)) if isinstance(a, (str, Path)) else a for a in args]

    for p in paths_to_create:
        if p is None:
            continue
        try:
            p = Path(p)
            p.mkdir(parents=True, exist_ok=True)
        except (TypeError, ValueError, OSError):
            # Silently ignore invalid paths to avoid breaking callers with bad args
            pass

def get_path(*args) -> Path:
    """
    Resolve a path based on the configuration.
    Accepts:
      - Single string key (e.g., "data_raw") -> returns Path from _PATHS
      - Single string relative path (e.g., "data/processed/features.csv") -> returns Path(root / rel)
      - Two args: (base_key, relative) -> returns Path(_PATHS[base_key] / relative)
      - Two args: (relative_str, relative_str) -> treats first as base relative to root
    """
    if not args:
        return _PATHS["root"]

    if len(args) == 1:
        key = args[0]
        if isinstance(key, str):
            # Check if it's a known key
            if key in _PATHS:
                return _PATHS[key]
            # Otherwise treat as relative to root
            return _PATHS["root"] / key
        elif isinstance(key, Path):
            return key
        else:
            return _PATHS["root"]

    if len(args) == 2:
        base = args[0]
        rel = args[1]

        # If base is a known key
        if isinstance(base, str) and base in _PATHS:
            return _PATHS[base] / rel

        # If base is a path-like string not in keys, assume relative to root
        if isinstance(base, str):
            return _PATHS["root"] / base / rel

        # If base is Path
        if isinstance(base, Path):
            return base / rel

        return _PATHS["root"] / str(base) / str(rel)

    # Fallback
    return _PATHS["root"]

# Filter Parameters
FILTER_PARAMS = {
    "l_freq": 1.0,
    "h_freq": 40.0,
    "notch_freq": 60.0,
    "filt_method": "fir",
    "pad": "reflect",
}

def get_filter_params() -> Dict[str, Any]:
    """Return filter parameters."""
    return FILTER_PARAMS.copy()

# ICA Parameters
ICA_PARAMS = {
    "n_components": 20,
    "method": "fastica",
    "random_state": 42,
    "max_iter": 1000,
}

def get_ica_params() -> Dict[str, Any]:
    """Return ICA parameters."""
    return ICA_PARAMS.copy()

# Exclusion Parameters
EXCLUSION_PARAMS = {
    "max_channel_rejection_ratio": 0.30,
}

def get_exclusion_params() -> Dict[str, Any]:
    """Return exclusion parameters."""
    return EXCLUSION_PARAMS.copy()

# Band Definitions (Hz)
BAND_FREQS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "low_beta": (13.0, 20.0),
    "high_beta": (20.0, 30.0),
    "gamma": (30.0, 45.0),
}

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Return band frequency definitions."""
    return BAND_FREQS.copy()

def get_all_band_names() -> List[str]:
    """Return list of all band names."""
    return list(BAND_FREQS.keys())

# Processing Parameters
WINDOW_SECONDS = 4.0
OVERLAP_SECONDS = 2.0
MIN_EPOCH_DURATION_MINUTES = 5
CV_FOLDS = 5

def get_window_seconds() -> float:
    """Return window size in seconds."""
    return WINDOW_SECONDS

def get_overlap_seconds() -> float:
    """Return overlap size in seconds."""
    return OVERLAP_SECONDS

def get_cv_folds() -> int:
    """Return number of CV folds."""
    return CV_FOLDS

def get_min_epoch_duration_minutes() -> int:
    """Return minimum epoch duration in minutes."""
    return MIN_EPOCH_DURATION_MINUTES

# Config file loading
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = _PATHS["root"] / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}
