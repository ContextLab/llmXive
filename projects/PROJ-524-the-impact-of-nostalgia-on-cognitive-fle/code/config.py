"""
Configuration management for the project.
Handles environment variables, paths, and runtime settings.

Note: Do not store runtime flags here (e.g., simulation_mode, exclusion counts).
Those belong in data metadata files (e.g., data/raw/metadata.json).
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from utils import setup_logging, log_info, log_warning


def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    
    Returns:
        Dictionary containing configuration parameters.
    """
    base_path = os.getenv("PROJECT_ROOT", ".")
    
    config = {
        "base_path": base_path,
        "data_path": os.path.join(base_path, "data"),
        "code_path": os.path.join(base_path, "code"),
        "tests_path": os.path.join(base_path, "tests"),
        "contracts_path": os.path.join(base_path, "contracts"),
        "paper_path": os.path.join(base_path, "paper"),
        "mmse_threshold": get_env_int("MMSE_THRESHOLD", 24),
        "data_source_url": get_env_str("DATA_SOURCE_URL", ""),
        "log_level": get_log_level(),
    }
    
    return config


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if provided, otherwise use defaults.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Configuration dictionary.
    """
    if config_path and os.path.exists(config_path):
        import yaml
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            return {**get_config(), **file_config}
    return get_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = get_config()
    return config.get(key, default)


def get_env_str(key: str, default: str = "") -> str:
    """Get an environment variable as a string."""
    return os.getenv(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """Get an environment variable as an integer."""
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get an environment variable as a float."""
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean."""
    val = os.getenv(key, str(default)).lower()
    return val in ('true', '1', 'yes', 'on')


def get_mmse_threshold() -> int:
    """Get the MMSE threshold for cognitive impairment."""
    return get_env_int("MMSE_THRESHOLD", 24)


def get_data_source_url() -> str:
    """Get the data source URL from environment."""
    return get_env_str("DATA_SOURCE_URL", "")


def get_log_level() -> int:
    """Get the logging level from environment."""
    level_str = get_env_str("LOG_LEVEL", "INFO").upper()
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str, logging.INFO)


def ensure_dirs():
    """
    Ensure all required directories exist.
    This is a helper that can be called during initialization.
    """
    config = get_config()
    required_dirs = [
        config["data_path"],
        os.path.join(config["data_path"], "raw"),
        os.path.join(config["data_path"], "processed"),
        os.path.join(config["data_path"], "results"),
        os.path.join(config["data_path"], "stimuli"),
        config["code_path"],
        config["tests_path"],
        config["contracts_path"],
        config["paper_path"],
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)