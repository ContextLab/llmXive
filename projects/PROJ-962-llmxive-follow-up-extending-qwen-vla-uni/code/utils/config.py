import os
import yaml
from typing import Dict, Any, Optional

_config: Optional[Dict[str, Any]] = None
_config_path: Optional[str] = None

def get_config_path() -> str:
    """
    Get the path to the configuration file.
    
    Returns:
        Path to the config file.
    """
    global _config_path
    if _config_path is None:
        # Default path relative to project root
        _config_path = os.path.join("data", "config.yaml")
    return _config_path

def load_config_from_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default.
        
    Returns:
        Configuration dictionary.
    """
    global _config, _config_path
    path = config_path or get_config_path()
    _config_path = path
    
    if not os.path.exists(path):
        # Return default config if file doesn't exist
        return _get_default_config()
        
    with open(path, 'r') as f:
        _config = yaml.safe_load(f)
        
    return _config

def _get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values.
    
    Returns:
        Default configuration dictionary.
    """
    return {
        "data": {
            "dataset_name": "Qwen-VLA/Hy-Embodied",
            "streaming": True,
            "batch_size": 1024
        },
        "clustering": {
            "max_k": 50,
            "min_silhouette": 0.25,
            "k_reduction_step_size": 5,
            "max_k_reduction_attempts": 10
        },
        "simulation": {
            "dt": 0.02,
            "max_steps": 500,
            "joint_limits": {
                "lower": -3.14,
                "upper": 3.14
            }
        }
    }

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_config_from_file()
    return _config

def set_config_value(key: str, value: Any) -> None:
    """
    Set a configuration value.
    
    Args:
        key: Dot-separated key path (e.g., "clustering.max_k").
        value: Value to set.
    """
    global _config
    if _config is None:
        _config = _get_default_config()
        
    keys = key.split('.')
    current = _config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value

def get_clustering_params() -> Dict[str, Any]:
    """
    Get clustering-specific parameters.
    
    Returns:
        Dictionary of clustering parameters.
    """
    config = get_config()
    return config.get("clustering", {})

def get_data_params() -> Dict[str, Any]:
    """
    Get data loading parameters.
    
    Returns:
        Dictionary of data parameters.
    """
    config = get_config()
    return config.get("data", {})

def get_simulation_params() -> Dict[str, Any]:
    """
    Get simulation parameters.
    
    Returns:
        Dictionary of simulation parameters.
    """
    config = get_config()
    return config.get("simulation", {})