import os
import json
import random
import hashlib
import numpy as np
from typing import Dict, Any, Optional

# Global configuration state
_seed: Optional[int] = None
_version_hash: str = ""
_config: Dict[str, Any] = {
    "tiers": {
        "tier_1": {
            "nodes": (5, 10),
            "stochastic": False,
            "path_count": 1
        },
        "tier_2": {
            "nodes": (15, 30),
            "stochastic": True,
            "path_count": 3
        },
        "tier_3": {
            "nodes": (50, 100),
            "stochastic": True,
            "path_count": 10,
            "sparsity": 0.1
        }
    },
    "experiment": {
        "episodes_per_setting": 1000,
        "threshold_step": 0.1,
        "threshold_min": 0.0,
        "threshold_max": 1.0
    }
}

def set_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    global _seed
    _seed = seed
    random.seed(seed)
    np.random.seed(seed)
    _version_hash = hashlib.sha256(f"{seed}_v1.0".encode()).hexdigest()[:16]

def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.
    
    Returns:
        The current seed integer, or None if not set.
    """
    return _seed

def get_version_hash() -> str:
    """
    Get the version hash derived from the current seed.
    
    Returns:
        Hex string version hash.
    """
    return _version_hash

def get_tier_config(tier_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific complexity tier.
    
    Args:
        tier_name: Name of the tier (e.g., 'tier_1', 'tier_2', 'tier_3').
        
    Returns:
        Dictionary containing tier configuration.
        
    Raises:
        KeyError: If tier_name is not found.
    """
    if tier_name not in _config["tiers"]:
        raise KeyError(f"Tier '{tier_name}' not found in configuration.")
    return _config["tiers"][tier_name]

def ensure_directories() -> None:
    """
    Create necessary directory structure for data and logs.
    """
    dirs = [
        "data/raw/synthetic_graphs",
        "data/processed",
        "data/logs",
        "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def save_config_snapshot(output_path: str) -> None:
    """
    Save the current configuration to a JSON file.
    
    Args:
        output_path: Path where the config snapshot will be saved.
    """
    snapshot = {
        "seed": _seed,
        "version_hash": _version_hash,
        "config": _config
    }
    with open(output_path, 'w') as f:
        json.dump(snapshot, f, indent=2)

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Returns:
        Dictionary with seed, version hash, and tier names.
    """
    return {
        "seed": _seed,
        "version_hash": _version_hash,
        "tiers": list(_config["tiers"].keys())
    }
