"""
Configuration management for the llmXive pipeline.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from utils import setup_logging

logger = setup_logging()

# Default paths relative to project root
DEFAULT_CONFIG = {
    'paths': {
        'root': Path.cwd(),
        'raw': Path('data/raw'),
        'processed': Path('data/processed'),
        'results': Path('data/results'),
        'stimuli': Path('data/stimuli'),
        'contracts': Path('contracts'),
        'code': Path('code'),
        'tests': Path('tests'),
        'paper': Path('paper')
    },
    'thresholds': {
        'mmse': 24,
        'age_min': 65
    }
}

def get_env_str(key: str, default: Optional[str] = None) -> str:
    """Get a string environment variable."""
    return os.environ.get(key, default or "")

def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer environment variable."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        logger.warning(f"Invalid integer for env var {key}, using default: {default}")
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get a float environment variable."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        logger.warning(f"Invalid float for env var {key}, using default: {default}")
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean environment variable."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes', 'on')

def get_mmse_threshold() -> int:
    """Get the MMSE threshold from config or environment."""
    return get_env_int('MMSE_THRESHOLD', DEFAULT_CONFIG['thresholds']['mmse'])

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    
    Returns:
        Configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override paths if environment variables are set
    if 'PROJECT_ROOT' in os.environ:
        config['paths']['root'] = Path(os.environ['PROJECT_ROOT'])
    
    return config

def get_config() -> Dict[str, Any]:
    """Get the full configuration."""
    return load_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific value from the configuration using dot notation.
    e. g. 'paths.raw' -> config['paths']['raw']
    """
    config = get_config()
    keys = key.split('.')
    val = config
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val

def ensure_dirs(config: Dict[str, Any]) -> None:
    """Ensure all required directories exist based on config."""
    from utils import ensure_dirs
    paths = [config['paths'][k] for k in config['paths']]
    ensure_dirs(paths)
    logger.info("Directories ensured.")
