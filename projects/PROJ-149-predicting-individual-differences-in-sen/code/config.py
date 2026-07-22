"""
Configuration management for the EEG Sensory Speed project.
Defines paths, filter parameters, band definitions, and random seeds.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.yaml"

# Global Seed
_GLOBAL_SEED = 42

def set_global_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """Get the current global seed."""
    return _GLOBAL_SEED

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml if it exists."""
    if not CONFIG_FILE.exists():
        # Return defaults if config file is missing
        return {
            "paths": {
                "data_raw": "data/raw",
                "data_interim": "data/interim",
                "data_processed": "data/processed",
                "figures": "figures",
                "code": "code"
            },
            "filter_params": {
                "low_cut": 1.0,
                "high_cut": 40.0,
                "notch_freqs": [50.0, 60.0],
                "variance_threshold": 3.0
            },
            "bands": {
                "delta": (1.0, 4.0),
                "theta": (4.0, 8.0),
                "alpha": (8.0, 13.0),
                "low_beta": (13.0, 20.0),
                "high_beta": (20.0, 30.0),
                "gamma": (30.0, 40.0)
            }
        }
    
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    config = load_config()
    for key, path_str in config.get("paths", {}).items():
        path = PROJECT_ROOT / path_str
        path.mkdir(parents=True, exist_ok=True)

def get_path(key: str) -> Path:
    """
    Get a specific path from the configuration.
    
    Args:
        key: The key in the 'paths' section of config.yaml.
             Special keys: 'features_raw', 'features', 'feasibility_report'
    
    Returns:
        Absolute Path object.
    """
    config = load_config()
    paths_cfg = config.get("paths", {})
    
    # Handle special derived paths
    if key == 'features_raw':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'features_raw.csv'
    elif key == 'features':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'features.csv'
    elif key == 'feasibility_report':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'feasibility_report.md'
    elif key == 'model_results':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'model_results.json'
    elif key == 'split_indices':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'split_indices.json'
    elif key == 'final_report':
        return PROJECT_ROOT / paths_cfg.get('data_processed', 'data/processed') / 'final_report.md'
    
    base_path = paths_cfg.get(key)
    if not base_path:
        raise KeyError(f"Path key '{key}' not found in config.")
    
    return PROJECT_ROOT / base_path

def get_filter_params() -> Dict[str, Any]:
    """Get EEG filter parameters."""
    config = load_config()
    return config.get("filter_params", {
        "low_cut": 1.0,
        "high_cut": 40.0,
        "notch_freqs": [50.0, 60.0],
        "variance_threshold": 3.0
    })

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency definitions for EEG bands."""
    config = load_config()
    return config.get("bands", {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "low_beta": (13.0, 20.0),
        "high_beta": (20.0, 30.0),
        "gamma": (30.0, 40.0)
    })

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(get_band_freqs().keys())
