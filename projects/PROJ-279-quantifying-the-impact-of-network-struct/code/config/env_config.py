import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

class ConfigError(Exception):
    pass

class EnvironmentConfig:
    def __init__(self):
        self._config = {
            'cutoff_radius': float(os.getenv('CUTOFF_RADIUS', '3.0')),
            'zenodo_url': os.getenv('ZENODO_URL', ''),
            'data_dir': os.getenv('DATA_DIR', 'data'),
            'processed_dir': os.getenv('PROCESSED_DIR', 'data/processed'),
            'log_file': os.getenv('LOG_FILE', 'logs/analysis.log'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'metadata_url': os.getenv('METADATA_URL', ''),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

# Global config instance
_config_instance: Optional[EnvironmentConfig] = None

def get_config() -> EnvironmentConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance

def reload_config() -> EnvironmentConfig:
    global _config_instance
    _config_instance = EnvironmentConfig()
    return _config_instance

def get_cutoff_radius() -> float:
    return get_config().get('cutoff_radius', 3.0)

def get_zenodo_url() -> str:
    return get_config().get('zenodo_url', '')

def get_data_dir() -> Path:
    return Path(get_config().get('data_dir', 'data'))

def get_processed_dir() -> Path:
    return Path(get_config().get('processed_dir', 'data/processed'))

def get_log_file_path() -> Path:
    return Path(get_config().get('log_file', 'logs/analysis.log'))

def get_log_level() -> int:
    level_str = get_config().get('log_level', 'INFO')
    return getattr(logging, level_str.upper(), logging.INFO)

def main():
    """
    Entry point for environment config.
    """
    cfg = get_config()
    print(f"Cutoff Radius: {cfg.get('cutoff_radius')}")
    print(f"Zenodo URL: {cfg.get('zenodo_url')}")
    print(f"Data Dir: {cfg.get('data_dir')}")
    return 0
