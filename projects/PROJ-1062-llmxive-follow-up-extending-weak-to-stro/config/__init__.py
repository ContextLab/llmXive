"""
Configuration module for the llmXive pipeline.

This module provides access to configuration defaults and
environment-based overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to config/defaults.yaml
    
    Returns:
        Dictionary with configuration values
    """
    if config_path is None:
        config_path = Path(__file__).parent / "defaults.yaml"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Environment variable overrides
    for key in config:
        env_key = f"LLMXIVE_{key.upper()}"
        if env_key in os.environ:
            config[key] = os.environ[env_key]
    
    return config

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key (supports dot notation)
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    config = load_config()
    
    parts = key.split('.')
    value = config
    
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
    
    return value

__all__ = ['load_config', 'get_config_value']
