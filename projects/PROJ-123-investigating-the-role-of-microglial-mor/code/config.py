import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import random
import numpy as np

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration Defaults
DEFAULT_CONFIG = {
    "seed": 42,
    "cpu_only": True,
    "paths": {
        "data_root": "data",
        "model_root": "models",
        "reports": "reports",
        "specs": "specs",
        "code": "code",
        "tests": "tests"
    },
    "morphometry": {
        "sholl_radii": [2, 5, 10],
        "denoise_sigma": 1.0,
        "background_subtract": True
    },
    "analysis": {
        "vif_threshold": 5.0,
        "cv_folds": 5,
        "random_state": 42
    }
}

CONFIG: Dict[str, Any] = {}

def get_project_root() -> Path:
    """Get the project root directory."""
    return _PROJECT_ROOT

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.
    
    Args:
        config_path: Path to config file. If None, uses default.
    
    Returns:
        Dict: Configuration dictionary.
    """
    global CONFIG
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            CONFIG = yaml.safe_load(f)
    else:
        CONFIG = DEFAULT_CONFIG
    return CONFIG

def get_path(*relative_parts: str) -> Path:
    """
    Construct an absolute path relative to the project root.
    
    Args:
        relative_parts: Path components relative to project root.
    
    Returns:
        Path: Absolute path.
    """
    return _PROJECT_ROOT / os.path.join(*relative_parts)

def ensure_dirs(*path_strs: str) -> Path:
    """
    Ensure directories exist for the given paths.
    
    Args:
        path_strs: Path strings to ensure exist.
    
    Returns:
        Path: The last path created/checked.
    """
    for p_str in path_strs:
        p = get_path(p_str)
        p.mkdir(parents=True, exist_ok=True)
    return get_path(*path_strs)

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = DEFAULT_CONFIG.get("seed", 42)
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_morphometry_config() -> Dict[str, Any]:
    """Get morphometry specific configuration."""
    return DEFAULT_CONFIG.get("morphometry", {})

def get_analysis_config() -> Dict[str, Any]:
    """Get analysis specific configuration."""
    return DEFAULT_CONFIG.get("analysis", {})

def get_data_paths() -> Dict[str, str]:
    """Get data directory paths."""
    return DEFAULT_CONFIG.get("paths", {})

# T004: Explicit constants for paths, seeds, and CPU-only execution
DATA_ROOT = get_path(DEFAULT_CONFIG["paths"]["data_root"])
MODEL_ROOT = get_path(DEFAULT_CONFIG["paths"]["model_root"])
SEED = DEFAULT_CONFIG["seed"]
CPU_ONLY = DEFAULT_CONFIG["cpu_only"]

# Ensure required directories exist on import (idempotent)
ensure_dirs(
    DEFAULT_CONFIG["paths"]["data_root"],
    os.path.join(DEFAULT_CONFIG["paths"]["data_root"], "raw"),
    os.path.join(DEFAULT_CONFIG["paths"]["data_root"], "processed"),
    os.path.join(DEFAULT_CONFIG["paths"]["data_root"], "intermediates"),
    DEFAULT_CONFIG["paths"]["reports"],
    DEFAULT_CONFIG["paths"]["specs"],
    DEFAULT_CONFIG["paths"]["tests"]
)