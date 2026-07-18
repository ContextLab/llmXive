"""
Configuration defaults and loading utilities.

Provides access to default hyperparameters defined in defaults.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses defaults.yaml from project root.
        
    Returns:
        Dictionary containing configuration parameters.
    """
    if config_path is None:
        # Try to find defaults.yaml in standard locations
        possible_paths = [
            Path("src/config/defaults.yaml"),
            Path("config/defaults.yaml"),
            Path("defaults.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            # Return default values if no config file found
            return get_default_config()
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def get_default_config() -> Dict[str, Any]:
    """
    Return default configuration values.
    
    Returns:
        Dictionary with default hyperparameters.
    """
    return {
        "simulation": {
            "n_objectives": [5, 10, 20, 50],
            "window_size_ratios": [0.1, 0.2, 0.5],
            "seeds": [42, 123, 456],
            "noise_correlation": [0.0, 0.2, 0.5],
            "num_episodes": 100,
            "max_steps_per_episode": 200
        },
        "heuristic": {
            "default_window_size": 10
        },
        "analysis": {
            "stability_threshold": 0.1,
            "stability_percentage": 0.95
        }
    }

# Global config instance
_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get global configuration (lazy loading).
    
    Returns:
        Configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
