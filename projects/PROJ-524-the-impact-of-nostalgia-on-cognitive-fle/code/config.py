import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_config() -> Dict[str, Any]:
    """
    Retrieves the base configuration for the project.
    Defaults to the current working directory if no env var is set.
    """
    base_path = os.getenv('PROJECT_ROOT', str(Path.cwd()))
    return {
        'base_path': base_path,
        'data_dir': os.path.join(base_path, 'data'),
        'contracts_dir': os.path.join(base_path, 'contracts'),
        'code_dir': os.path.join(base_path, 'code'),
        'tests_dir': os.path.join(base_path, 'tests'),
        'paper_dir': os.path.join(base_path, 'paper')
    }

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads configuration from a YAML file if provided."""
    if not config_path:
        return get_config()
    
    # Implementation for YAML loading would go here
    # For now, return base config
    return get_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """Gets a specific value from the config."""
    config = get_config()
    return config.get(key, default)

def get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Gets a string environment variable."""
    return os.getenv(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """Gets an integer environment variable."""
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Gets a float environment variable."""
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default

def get_env_bool(key: str, default: bool = False) -> bool:
    """Gets a boolean environment variable."""
    val = os.getenv(key, str(default)).lower()
    return val in ('true', '1', 'yes', 'on')

def get_mmse_threshold() -> int:
    """Returns the MMSE threshold for cognitive impairment."""
    return get_env_int('MMSE_THRESHOLD', 24)

def ensure_dirs(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensures all required directories exist based on config.
    This is a helper for T001 to verify directories.
    """
    if config is None:
        config = get_config()
    
    dirs_to_create = [
        config.get('data_dir'),
        os.path.join(config.get('data_dir'), 'raw'),
        os.path.join(config.get('data_dir'), 'processed'),
        os.path.join(config.get('data_dir'), 'results'),
        os.path.join(config.get('data_dir'), 'stimuli'),
        config.get('contracts_dir'),
        config.get('code_dir'),
        config.get('tests_dir'),
        config.get('paper_dir')
    ]
    
    for dir_path in dirs_to_create:
        if dir_path:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Verified directory: {dir_path}")