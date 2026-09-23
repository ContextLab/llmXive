"""
Configuration management module.
Handles environment variables, paths, and project settings.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    Returns a dictionary of configuration values.
    """
    # Default project root is the current working directory
    project_root = os.getenv('PROJECT_ROOT', '.')
    
    config = {
        'project_root': str(Path(project_root).resolve()),
        'data_dir': os.getenv('DATA_DIR', 'data'),
        'code_dir': os.getenv('CODE_DIR', 'code'),
        'tests_dir': os.getenv('TESTS_DIR', 'tests'),
        'contracts_dir': os.getenv('CONTRACTS_DIR', 'contracts'),
        'paper_dir': os.getenv('PAPER_DIR', 'paper'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }
    
    return config

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file (e.g., config.yaml) if provided.
    Falls back to environment variables and defaults.
    """
    config = get_config()
    
    if config_path and os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    
    return config

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = get_config()
    return config.get(key, default)

def get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable as a string."""
    return os.getenv(key, default)

def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """Get an environment variable as an integer."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid integer for env var {key}: {value}")
        return default

def get_env_float(key: str, default: Optional[float] = None) -> Optional[float]:
    """Get an environment variable as a float."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning(f"Invalid float for env var {key}: {value}")
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean."""
    value = os.getenv(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    elif value in ('false', '0', 'no', 'off'):
        return False
    return default

def get_mmse_threshold() -> int:
    """Get the MMSE threshold from environment or default to 24."""
    return get_env_int('MMSE_THRESHOLD', 24)

def ensure_dirs(*dirs: str) -> bool:
    """
    Ensure that the given directories exist.
    Creates them if they don't.
    """
    config = get_config()
    project_root = Path(config['project_root'])
    
    for dir_path in dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            return False
    return True
