"""
Configuration loader for the EEG pipeline.
Handles loading of pipeline_config.yaml and environment variables.
"""
import os
import yaml
from typing import Any, Dict, Optional

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the pipeline configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'pipeline_config.yaml' in the project root.
        
    Returns:
        Dictionary containing the configuration.
    """
    if config_path is None:
        # Assume project root is two levels up from code/config.py
        config_path = os.path.join(os.path.dirname(__file__), '..', 'pipeline_config.yaml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.
    
    Args:
        key: The environment variable name.
        default: Default value if not found.
        
    Returns:
        The value of the environment variable or default.
    """
    return os.getenv(key, default)

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a nested value from the config dictionary using dot notation.
    
    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path to the value (e.g., 'signal_processing.bandpass.low_cutoff').
        default: Default value if path not found.
        
    Returns:
        The value at the path or default.
    """
    keys = key_path.split('.')
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value
