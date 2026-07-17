import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import random
import numpy as np

# Project root is the parent of the 'code' directory
_PROJECT_ROOT: Optional[Path] = None

# CPU-only execution constraints
CPU_ONLY = True
MAX_WORKERS = 4  # Limit parallel workers for CPU constraint
MAX_MEMORY_GB = 14  # Approximate RAM limit for runner

# Random seeds for reproducibility
DEFAULT_SEED = 42

# Configuration dictionary
CONFIG: Dict[str, Any] = {}

def get_project_root() -> Path:
    """Returns the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Assume code/ is at root level or src/code/
        current_file = Path(__file__).resolve()
        # Try to find the project root by looking for 'tasks.md' or 'plan.md'
        # Common structure: projects/PROJ-.../code/config.py
        # Or: code/config.py
        parent = current_file.parent
        while parent != parent.parent:
            if (parent / "tasks.md").exists() or (parent / "plan.md").exists():
                _PROJECT_ROOT = parent
                break
            parent = parent.parent
        
        if _PROJECT_ROOT is None:
            # Fallback: assume current directory is project root
            _PROJECT_ROOT = Path.cwd()
    return _PROJECT_ROOT

def get_default_config() -> Dict[str, Any]:
    """Returns the default configuration dictionary."""
    return {
        "seed": DEFAULT_SEED,
        "cpu_only": CPU_ONLY,
        "max_workers": MAX_WORKERS,
        "max_memory_gb": MAX_MEMORY_GB,
        "paths": {
            "data_raw": "data/raw",
            "data_intermediates": "data/intermediates",
            "data_processed": "data/processed",
            "figures": "figures",
            "reports": "reports",
            "specs": "specs"
        },
        "morphometry": {
            "sholl_radii": [2, 5, 10],  # in micrometers
            "denoise_sigma": 1.0,
            "skeletonize_method": "zhang"
        },
        "analysis": {
            "vif_threshold": 5.0,
            "early_ad_amyloid_percentile": 75,
            "cv_folds": 5
        }
    }

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads configuration from a YAML file or returns defaults."""
    global CONFIG
    if CONFIG:
        return CONFIG
    
    if config_path is None:
        config_path = os.path.join(get_project_root(), "config.yaml")
    
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r") as f:
            CONFIG = yaml.safe_load(f)
    else:
        CONFIG = get_default_config()
    
    return CONFIG

def get_path(relative_path: str) -> Path:
    """Returns an absolute path relative to the project root."""
    return get_project_root() / relative_path

def ensure_dirs() -> None:
    """Creates all necessary directories defined in the configuration."""
    config = load_config()
    paths = config.get("paths", {})
    
    for dir_name in paths.values():
        dir_path = get_path(dir_name)
        dir_path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: Optional[int] = None) -> None:
    """Sets random seeds for reproducibility."""
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_morphometry_config() -> Dict[str, Any]:
    """Returns morphometry-specific configuration."""
    config = load_config()
    return config.get("morphometry", get_default_config()["morphometry"])

def get_analysis_config() -> Dict[str, Any]:
    """Returns analysis-specific configuration."""
    config = load_config()
    return config.get("analysis", get_default_config()["analysis"])

def get_data_paths() -> Dict[str, Path]:
    """Returns paths for data directories."""
    config = load_config()
    paths = config.get("paths", {})
    return {k: get_path(v) for k, v in paths.items()}