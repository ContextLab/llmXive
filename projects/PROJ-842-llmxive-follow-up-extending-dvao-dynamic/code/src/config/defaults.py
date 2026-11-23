"""
Configuration defaults for the llmXive project.
This module provides a centralized place for hyperparameters and settings.
"""
import os
import yaml
from typing import Dict, Any, Optional

# Try to import the YAML file if it exists, otherwise use defaults
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "defaults.yaml")

DEFAULTS: Dict[str, Any] = {
    "n_objectives": [5, 10, 20, 50],
    "k": 10,  # Window size for moving window heuristic
    "k_sweep": [0.01, 0.05, 0.1],  # Ratios of rollout size
    "seeds": [42, 123, 456],
    "noise_correlation": [0.0, 0.2, 0.5],
    "rollout_group_size": 100,
    "memory_limit_gb": 7,
    "cpu_cores": 2,
}

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        path: Path to the YAML file. If None, uses default CONFIG_PATH.
    
    Returns:
        Dictionary of configuration values.
    """
    if path is None:
        path = CONFIG_PATH
    
    if not os.path.exists(path):
        return DEFAULTS.copy()
    
    try:
        with open(path, 'r') as f:
            loaded = yaml.safe_load(f)
            if loaded is None:
                return DEFAULTS.copy()
            # Merge with defaults to ensure all keys exist
            config = DEFAULTS.copy()
            config.update(loaded)
            return config
    except Exception as e:
        print(f"Warning: Could not load config from {path}: {e}. Using defaults.")
        return DEFAULTS.copy()

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Dictionary of configuration values.
    """
    return load_config()

# Expose defaults directly for convenience
k = DEFAULTS["k"]
n_objectives = DEFAULTS["n_objectives"]
seeds = DEFAULTS["seeds"]
noise_correlation = DEFAULTS["noise_correlation"]
