"""
Configuration management for the llmXive Phase-Change Materials pipeline.

This module handles loading, validating, and accessing the project's
configuration settings (API keys, seeds, constraints) from a YAML file.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Default paths relative to project root
CONFIG_PATH = Path("config.yaml")
DEFAULT_CONFIG_TEMPLATE = {
    "project": {
        "name": "investigating-the-predictive-power-of-ma",
        "version": "0.1.0",
        "seed": 42,
    },
    "api": {
        "materials_project": {
            "api_key": os.getenv("MP_API_KEY", ""),
            "timeout": 30,
            "rate_limit_delay": 1.0,
        },
    },
    "constraints": {
        "max_memory_gb": 7.0,
        "max_time_hours": 4.0,
        "max_samples": 10000,
    },
    "paths": {
        "data_root": "data",
        "code_root": "code",
        "results_root": "data/results",
        "figures_root": "figures",
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in the project root.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if config_path is None:
        config_path = CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Merge with defaults to ensure all keys exist
    _config_cache = _deep_merge(DEFAULT_CONFIG_TEMPLATE, config)
    return _config_cache

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.

    Args:
        base: The base dictionary.
        override: The dictionary to merge on top.

    Returns:
        A new merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        The configuration dictionary.

    Raises:
        RuntimeError: If the config has not been loaded yet.
    """
    global _config_cache
    if _config_cache is None:
        # Attempt to load it if not already loaded
        try:
            load_config()
        except FileNotFoundError:
            # If file is missing, we might be in a setup phase or testing environment
            # Return a copy of defaults to avoid crashes, but log a warning in real usage
            import logging
            logging.warning("Config file not found, using defaults. Run setup if needed.")
            _config_cache = DEFAULT_CONFIG_TEMPLATE
    return _config_cache

def save_config_template(output_path: Optional[Path] = None) -> None:
    """
    Save a template configuration file to disk.

    This is useful for initializing a new project or resetting configuration.

    Args:
        output_path: Path to save the template. Defaults to 'config.yaml'.
    """
    if output_path is None:
        output_path = CONFIG_PATH

    with open(output_path, "w") as f:
        yaml.dump(DEFAULT_CONFIG_TEMPLATE, f, default_flow_style=False, sort_keys=False)

def get_api_key(service: str = "materials_project") -> str:
    """
    Retrieve an API key for a specific service.

    Args:
        service: The service name (e.g., 'materials_project').

    Returns:
        The API key string.

    Raises:
        KeyError: If the service is not found in config.
        ValueError: If the API key is empty.
    """
    config = get_config()
    try:
        key = config["api"][service]["api_key"]
        if not key:
            raise ValueError(f"API key for '{service}' is empty in config.")
        return key
    except KeyError:
        raise KeyError(f"Service '{service}' not found in configuration.")

def get_random_seed() -> int:
    """
    Get the global random seed for reproducibility.

    Returns:
        The integer seed value.
    """
    return get_config()["project"]["seed"]

def get_memory_limit_gb() -> float:
    """
    Get the maximum allowed memory usage in GB.

    Returns:
        The memory limit as a float.
    """
    return get_config()["constraints"]["max_memory_gb"]

def get_time_limit_hours() -> float:
    """
    Get the maximum allowed execution time in hours.

    Returns:
        The time limit as a float.
    """
    return get_config()["constraints"]["max_time_hours"]
