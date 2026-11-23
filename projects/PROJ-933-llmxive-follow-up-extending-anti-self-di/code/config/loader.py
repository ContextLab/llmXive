"""
Configuration loader module for llmXive.

Handles loading and validating the project settings from YAML.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

# Default relative path to config file
DEFAULT_CONFIG_PATH = Path(__file__).parent / "settings.yaml"

def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, uses the default 
                     settings.yaml in the config directory.
                     
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    else:
        config_path = Path(config_path)
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    # Basic validation: Ensure critical keys exist
    required_keys = ['seed', 'timeout_hours', 'training', 'data']
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"Configuration missing required keys: {missing_keys}")
        
    return config
