"""
Configuration management for the project.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_PATH = DATA_ROOT / "raw"
DERIVED_PATH = DATA_ROOT / "derived"
VALIDATION_PATH = DATA_ROOT / "validation"

# Default configuration
DEFAULT_CONFIG = {
    "sample_projects": [
        "python/cpython",
        "numpy/numpy",
        "pandas-dev/pandas",
        "scikit-learn/scikit-learn",
        "matplotlib/matplotlib"
    ],
    "min_events": 10,
    "sample_size": 100,
    "deferred_threshold": 5.0,
    "data_raw_path": str(RAW_PATH),
    "data_derived_path": str(DERIVED_PATH),
    "data_validation_path": str(VALIDATION_PATH)
}

_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    global _config
    if _config is None:
        # Try to load from a config file if it exists, otherwise use defaults
        config_file = PROJECT_ROOT / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                _config = json.load(f)
        else:
            _config = DEFAULT_CONFIG.copy()
    return _config

def ensure_directories_exist():
    """Creates the necessary data directories if they don't exist."""
    for path in [RAW_PATH, DERIVED_PATH, VALIDATION_PATH]:
        path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> str:
    cfg = get_config()
    return f"Config: min_events={cfg.get('min_events')}, projects={len(cfg.get('sample_projects', []))}"
