import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or defaults.
    Returns a dictionary of configuration values.
    """
    config = {
        'base_path': Path(os.getenv('PROJECT_ROOT', Path.cwd())),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'mmse_threshold': int(os.getenv('MMSE_THRESHOLD', '24')),
    }
    return config

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML/JSON file if provided."""
    if config_path and config_path.exists():
        # Placeholder for actual YAML/JSON loading
        # In a real implementation, we'd use yaml or json library
        pass
    return get_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific config value by key."""
    config = get_config()
    return config.get(key, default)

def get_env_str(key: str, default: Optional[str] = None) -> str:
    """Get an environment variable as a string."""
    return os.getenv(key, default) if default else os.getenv(key)

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
    """Get the MMSE threshold from config."""
    return get_config_value('mmse_threshold', 24)

def ensure_dirs(base_path: Optional[Path] = None) -> None:
    """Ensure base directories exist (placeholder)."""
    if base_path is None:
        base_path = get_config_value('base_path')
    # Actual directory creation is handled in setup_dirs.py
    pass
