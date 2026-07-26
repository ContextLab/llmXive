"""
Configuration management for the project.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from utils import setup_logging, log_info, log_warning

_config: Optional[Dict[str, Any]] = None
_logger: Optional[logging.Logger] = None


def load_config() -> Dict[str, Any]:
    """
    Loads configuration from environment variables and defaults.
    """
    global _config
    if _config is not None:
        return _config

    _config = {
        "paths": {
            "raw": os.getenv("RAW_DATA_DIR", "data/raw"),
            "processed": os.getenv("PROCESSED_DATA_DIR", "data/processed"),
            "results": os.getenv("RESULTS_DATA_DIR", "data/results"),
            "stimuli": os.getenv("STIMULI_DIR", "data/stimuli"),
            "code": os.getenv("CODE_DIR", "code"),
            "tests": os.getenv("TESTS_DIR", "tests"),
        },
        "settings": {
            "min_age": int(os.getenv("MIN_AGE", "65")),
            "mmse_threshold": int(os.getenv("MMSE_THRESHOLD", "24")),
            "data_source_url": os.getenv("DATA_SOURCE_URL", ""),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
    }
    return _config


def get_config() -> Dict[str, Any]:
    """
    Returns the global configuration dictionary.
    """
    return load_config()


def get_env_str(key: str, default: str = "") -> str:
    """
    Retrieves a string environment variable.
    """
    return os.getenv(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """
    Retrieves an integer environment variable.
    """
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """
    Retrieves a float environment variable.
    """
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Retrieves a boolean environment variable.
    """
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    elif val in ("false", "0", "no"):
        return False
    return default


def get_mmse_threshold() -> int:
    """
    Returns the MMSE threshold for cognitive impairment filtering.
    """
    return get_env_int("MMSE_THRESHOLD", 24)


def get_data_source_url() -> str:
    """
    Returns the URL for the data source.
    """
    return get_env_str("DATA_SOURCE_URL", "")


def get_log_level() -> int:
    """
    Returns the logging level based on environment variable.
    """
    level_str = get_env_str("LOG_LEVEL", "INFO").upper()
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str, logging.INFO)


def ensure_dirs() -> None:
    """
    Ensures all required directories exist based on configuration.
    """
    config = get_config()
    paths = config.get("paths", {})
    
    for dir_name, dir_path in paths.items():
        path_obj = Path(dir_path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {path_obj}")
