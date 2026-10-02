import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "data_dir": "data",
    "contracts_dir": "contracts",
    "code_dir": "code",
    "tests_dir": "tests",
    "paper_dir": "paper",
    "raw_dir": "data/raw",
    "processed_dir": "data/processed",
    "results_dir": "data/results",
    "stimuli_dir": "data/stimuli",
    "mmse_threshold": 24,
    "age_threshold": 65,
    "alpha": 0.05,
    "power_target": 0.80,
}

_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """Get the project configuration."""
    global _config
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
        # Override with environment variables if set
        for key in _config:
            env_key = f"NXIVE_{key.upper()}"
            if env_key in os.environ:
                _config[key] = os.environ[env_key]
    return _config


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file if it exists."""
    import yaml
    path = Path(config_path)
    if path.exists():
        with open(path, 'r') as f:
            custom_config = yaml.safe_load(f)
        config = get_config()
        config.update(custom_config)
        return config
    return get_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = get_config()
    return config.get(key, default)


def get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a string environment variable."""
    return os.environ.get(key, default)


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """Get an integer environment variable."""
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer for env var {key}: {value}")
    return default


def get_env_float(key: str, default: Optional[float] = None) -> Optional[float]:
    """Get a float environment variable."""
    value = os.environ.get(key)
    if value is not None:
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float for env var {key}: {value}")
    return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean environment variable."""
    value = os.environ.get(key, "").lower()
    return value in ('true', '1', 'yes', 'on')


def get_mmse_threshold() -> int:
    """Get the MMSE threshold for cognitive impairment."""
    return int(get_config_value("mmse_threshold", 24))


def ensure_dirs(dirs: list) -> None:
    """Create directories if they don't exist."""
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {dir_path}")