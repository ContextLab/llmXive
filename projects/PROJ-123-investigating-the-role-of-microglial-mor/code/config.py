import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Project Root
# The project root is assumed to be the parent of the 'code' directory
# This allows the config to be imported from anywhere within the project tree
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Random Seeds
# Fixed seeds for reproducibility across CPU-only executions
RANDOM_SEED = 42
NP_RANDOM_SEED = 42

# CPU-Only Execution Constants
# Constraints to ensure the pipeline runs within memory and compute limits
# as per the project's CPU-only requirement.
MAX_WORKERS = 4  # Limit parallelism to avoid CPU saturation
MAX_MEMORY_GB = 8  # Soft limit for memory-intensive operations
CHUNK_SIZE = 1000  # Rows to process in chunks for large datasets

# Configuration Defaults
DEFAULT_CONFIG = {
    "random_seed": RANDOM_SEED,
    "cpu_workers": MAX_WORKERS,
    "max_memory_gb": MAX_MEMORY_GB,
    "image_processing": {
        "denoise_sigma": 1.0,
        "skeletonize_method": "zhang",
        "sholl_radii_step": 5.0,  # micrometers
        "sholl_max_radius": 50.0,
    },
    "analysis": {
        "vif_threshold": 5.0,
        "p_value_threshold": 0.05,
        "amyloid_beta_threshold_percentile": 75,
    },
    "paths": {
        "data_raw": "data/raw",
        "data_intermediate": "data/intermediates",
        "data_processed": "data/processed",
        "figures": "figures",
        "reports": "reports",
        "specs": "specs/001-gene-regulation",
        "contracts": "specs/001-gene-regulation/contracts",
    }
}

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if provided, otherwise return defaults.
    
    Args:
        config_path: Optional path to a custom config YAML file relative to project root.
    
    Returns:
        Merged configuration dictionary (file overrides defaults).
    """
    config = get_default_config()
    
    if config_path:
        full_path = get_project_root() / config_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Deep merge logic could be added here, 
                    # but for now, simple top-level override or key override
                    # is sufficient for most use cases.
                    # We will perform a shallow update for simplicity unless nested logic is required.
                    # To be safe, let's do a recursive update for nested dicts.
                    def deep_update(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                                deep_update(d[k], v)
                            else:
                                d[k] = v
                        return d
                    deep_update(config, file_config)
        else:
            # Log warning or raise? For now, just return defaults if file missing
            # but in a real pipeline, this might be an error depending on strictness.
            pass
    
    return config

def get_path(key: str, relative: bool = True) -> Path:
    """
    Construct a path based on a configuration key.
    
    Args:
        key: The key in DEFAULT_CONFIG['paths'] to look up.
        relative: If True, return path relative to project root. 
                  If False, return absolute path.
    
    Returns:
        Path object.
    
    Raises:
        KeyError: If the key is not found in paths configuration.
    """
    config = get_default_config()
    if key not in config['paths']:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    
    path_str = config['paths'][key]
    full_path = _PROJECT_ROOT / path_str
    
    if relative:
        # Return path relative to project root
        return Path(path_str)
    return full_path

def ensure_dirs(*keys: str) -> None:
    """
    Ensure that directories specified by configuration keys exist.
    
    Args:
        *keys: One or more keys from DEFAULT_CONFIG['paths'].
    
    Raises:
        KeyError: If a key is not found.
    """
    for key in keys:
        dir_path = get_path(key, relative=False)
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize random seeds immediately if this module is imported
import random
import numpy as np
random.seed(RANDOM_SEED)
np.random.seed(NP_RANDOM_SEED)

# Load global config instance (optional, but useful for functions needing config)
CONFIG = load_config()