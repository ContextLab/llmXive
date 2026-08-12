"""
Configuration management for the EEG Sensory Processing Speed project.
Handles paths, seeds, filter parameters, and band definitions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Band definitions (Hz)
BAND_FREQS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "low_beta": (13.0, 20.0),
    "high_beta": (20.0, 30.0),
    "gamma": (30.0, 45.0),
}
ALL_BAND_NAMES = list(BAND_FREQS.keys())

# Filter parameters
FILTER_PARAMS = {
    "low_cut": 1.0,
    "high_cut": 45.0,
    "notch_freq": 50.0,  # Change to 60.0 if needed for US data
    "l_trans_bandwidth": 1.0,
    "h_trans_bandwidth": 1.0,
}

# ICA parameters
ICA_PARAMS = {
    "method": "fastica",
    "n_components": 0.95,  # Explain 95% variance
    "random_state": 42,
}

# Exclusion parameters
EXCLUSION_PARAMS = {
    "channel_variance_threshold": 3.0,  # SD
    "max_rejected_ratio": 0.30,  # 30% channels rejected
    "min_trials_ratio": 0.70,  # 70% trials remaining
    "rt_min": 100.0,  # ms
    "rt_max": 2000.0,  # ms
}

# Windowing for PSD
WINDOW_PARAMS = {
    "window_seconds": 4.0,
    "overlap_seconds": 2.0,
}

# Modeling parameters
MODEL_PARAMS = {
    "cv_folds": 5,
    "random_state": 42,
}

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml if it exists, otherwise return defaults.
    Fixes the UnboundLocalError by ensuring _CONFIG is initialized before merge.
    """
    _CONFIG = {
        "paths": {
            "raw": str(PROJECT_ROOT / "data" / "raw"),
            "interim": str(PROJECT_ROOT / "data" / "interim"),
            "processed": str(PROJECT_ROOT / "data" / "processed"),
            "figures": str(PROJECT_ROOT / "figures"),
        },
        "bands": BAND_FREQS,
        "filter": FILTER_PARAMS,
        "ica": ICA_PARAMS,
        "exclusion": EXCLUSION_PARAMS,
        "window": WINDOW_PARAMS,
        "model": MODEL_PARAMS,
    }

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                custom_config = yaml.safe_load(f) or {}
            # Deep merge helper
            def _deep_merge(base: Dict, override: Dict) -> Dict:
                result = base.copy()
                for key, value in override.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = _deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            # Perform merge safely
            _CONFIG = _deep_merge(_CONFIG, custom_config)
        except Exception as e:
            print(f"Warning: Could not load custom config: {e}. Using defaults.")
    
    return _CONFIG

# Initialize config globally
_CONFIG = load_config()

def get_path(name: str) -> Path:
    """Get a path from the config."""
    path_str = _CONFIG["paths"].get(name)
    if not path_str:
        raise ValueError(f"Path '{name}' not found in config.")
    return Path(path_str)

def ensure_dirs():
    """Ensure all directories defined in config exist."""
    for key, path_str in _CONFIG["paths"].items():
        p = Path(path_str)
        p.mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """Get the global random seed."""
    return _CONFIG["model"].get("random_state", 42)

def set_global_seed(seed: Optional[int] = None):
    """Set the global random seed for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_filter_params() -> Dict[str, Any]:
    """Get EEG filter parameters."""
    return _CONFIG["filter"]

def get_ica_params() -> Dict[str, Any]:
    """Get ICA parameters."""
    return _CONFIG["ica"]

def get_exclusion_params() -> Dict[str, Any]:
    """Get exclusion criteria parameters."""
    return _CONFIG["exclusion"]

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency ranges for EEG bands."""
    return _CONFIG["bands"]

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return _CONFIG["bands"].keys()

def get_window_seconds() -> float:
    """Get window length in seconds."""
    return _CONFIG["window"]["window_seconds"]

def get_overlap_seconds() -> float:
    """Get overlap length in seconds."""
    return _CONFIG["window"]["overlap_seconds"]

def get_cv_folds() -> int:
    """Get number of CV folds."""
    return _CONFIG["model"]["cv_folds"]
