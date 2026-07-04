"""
Configuration management for the Lorentz Violation Testing pipeline.

This module handles loading, validating, and accessing project configuration
from a YAML file.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml


DEFAULT_CONFIG_PATH = Path("config.yaml")


REQUIRED_KEYS = {
    "paths": ["raw", "processed", "results", "simulations", "figures"],
    "seeds": ["random", "numpy"],
    "constants": ["sme_coefficient", "l_max"]
}


class ConfigError(Exception):
    """Raised when configuration validation fails."""
    pass


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and validate the configuration file.
    
    Args:
        config_path: Path to the YAML configuration file. If None, defaults to 'config.yaml'
                     in the current working directory.
                     
    Returns:
        A dictionary containing the validated configuration.
        
    Raises:
        ConfigError: If the file cannot be found, parsed, or fails validation.
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    if not isinstance(config_path, Path):
        config_path = Path(config_path)
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax in {config_path}: {e}")
        
    if not isinstance(config, dict):
        raise ConfigError(f"Configuration must be a dictionary, got {type(config).__name__}")
        
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that all required keys and sub-keys are present in the configuration.
    
    Args:
        config: The configuration dictionary to validate.
        
    Raises:
        ConfigError: If validation fails.
    """
    missing_sections = []
    for section, required_subkeys in REQUIRED_KEYS.items():
        if section not in config:
            missing_sections.append(section)
            continue
            
        if not isinstance(config[section], dict):
            raise ConfigError(f"Section '{section}' must be a dictionary.")
            
        missing_subkeys = [key for key in required_subkeys if key not in config[section]]
        if missing_subkeys:
            raise ConfigError(
                f"Missing required keys in '{section}': {', '.join(missing_subkeys)}"
            )
            
    if missing_sections:
        raise ConfigError(
            f"Missing required configuration sections: {', '.join(missing_sections)}"
        )


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Retrieve a value from the configuration using a dot-notation path.
    
    Args:
        config: The configuration dictionary.
        key_path: Dot-separated path to the value (e.g., 'paths.raw').
        default: Value to return if the key is not found.
        
    Returns:
        The value at the specified path, or the default if not found.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def enforce_seeds(config: Dict[str, Any]) -> None:
    """
    Enforce deterministic behavior by setting random seeds from the configuration.
    
    Reads the 'seeds' section from the config dictionary and sets the seeds
    for both the built-in `random` module and `numpy.random`.
    
    Args:
        config: The validated configuration dictionary containing a 'seeds' section.
                
    Raises:
        ConfigError: If the 'seeds' section is missing or values are invalid.
    """
    if "seeds" not in config:
        raise ConfigError("Configuration missing 'seeds' section required for enforce_seeds.")
    
    seeds = config["seeds"]
    
    if "random" not in seeds:
        raise ConfigError("Configuration missing 'seeds.random' value.")
    if "numpy" not in seeds:
        raise ConfigError("Configuration missing 'seeds.numpy' value.")
        
    random_seed = seeds["random"]
    numpy_seed = seeds["numpy"]
    
    # Validate that seeds are integers
    try:
        random_seed = int(random_seed)
        numpy_seed = int(numpy_seed)
    except (ValueError, TypeError) as e:
        raise ConfigError(f"Seed values must be integers. Got: random={random_seed}, numpy={numpy_seed}") from e
        
    random.seed(random_seed)
    np.random.seed(numpy_seed)