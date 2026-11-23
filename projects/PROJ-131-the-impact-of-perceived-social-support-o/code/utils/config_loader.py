"""
Configuration Loader Module
Provides utilities to load YAML configuration files for the pipeline.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file from the project root.

    Args:
        config_path: Relative path to the config file from project root.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    full_path = PROJECT_ROOT / config_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {full_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_seed() -> int:
    """
    Retrieve the random seed from the seeds configuration.

    Returns:
        The integer random seed.
    """
    config = load_yaml_config("code/config/seeds.yaml")
    if config is None:
        raise ValueError("Seeds configuration is empty or invalid.")
    return int(config.get("random_seed", 42))

def get_paths() -> Dict[str, str]:
    """
    Retrieve data path configuration.

    Returns:
        Dictionary of path configurations.
    """
    return load_yaml_config("code/config/data_paths.yaml")