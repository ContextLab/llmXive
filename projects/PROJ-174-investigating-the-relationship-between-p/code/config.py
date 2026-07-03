"""
Configuration loader for the project.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Default config file path
DEFAULT_CONFIG_PATH = "code/config.yaml"


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        Dictionary with configuration values
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config or {}
