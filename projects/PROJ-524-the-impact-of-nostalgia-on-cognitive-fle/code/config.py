import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Returns the project configuration.
    Defaults to root_dir='.' if not explicitly set.
    """
    global _config
    if _config is None:
        _config = {
            'root_dir': os.environ.get('PROJECT_ROOT', '.'),
            'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
            'mmse_threshold': int(os.environ.get('MMSE_THRESHOLD', 24))
        }
    return _config

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON/YAML file if provided.
    Falls back to defaults if file not found.
    """
    global _config
    if _config is None:
        _config = {
            'root_dir': '.',
            'log_level': 'INFO',
            'mmse_threshold': 24
        }
    
    if config_path:
        path = Path(config_path)
        if path.exists():
            # Simple JSON loader for now
            import json
            with open(path, 'r') as f:
                file_config = json.load(f)
                _config.update(file_config)
    return _config

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific config value."""
    return get_config().get(key, default)

def get_env_str(key: str, default: str = '') -> str:
    """Get environment variable as string."""
    return os.environ.get(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer."""
    try:
        return int(os.environ.get(key, default))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get environment variable as float."""
    try:
        return float(os.environ.get(key, default))
    except ValueError:
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    val = os.environ.get(key, str(default)).lower()
    return val in ('true', '1', 'yes', 'on')

def get_mmse_threshold() -> int:
    """Get the MMSE threshold from config."""
    return get_config_value('mmse_threshold', 24)

def ensure_dirs():
    """
    Ensure that all required directories exist.
    This is a helper to be called before file operations.
    """
    config = get_config()
    root = Path(config.get('root_dir', '.'))
    
    dirs = [
        'data/raw', 'data/processed', 'data/results', 'data/stimuli',
        'contracts', 'code', 'tests', 'paper'
    ]
    
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
    return True
