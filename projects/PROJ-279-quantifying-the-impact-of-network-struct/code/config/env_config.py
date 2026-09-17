import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Manages environment-based configuration for the project.
    Loads values from environment variables or defaults.
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from environment variables."""
        # Core paths
        self._config['project_root'] = Path(os.getenv('PROJECT_ROOT', Path(__file__).resolve().parent.parent.parent))
        self._config['data_dir'] = self._config['project_root'] / 'data'
        self._config['processed_dir'] = self._config['data_dir'] / 'processed'
        self._config['raw_dir'] = self._config['data_dir'] / 'raw'
        self._config['logs_dir'] = self._config['project_root'] / 'logs'
        
        # Parameters
        self._config['cutoff_radius'] = float(os.getenv('CUTOFF_RADIUS', '3.0'))
        self._config['zenodo_url'] = os.getenv('ZENODO_URL', 'https://zenodo.org/api/records/123456')
        self._config['log_level'] = os.getenv('LOG_LEVEL', 'INFO').upper()
        self._config['log_file'] = self._config['logs_dir'] / 'analysis.log'

        # Validation
        if not isinstance(self._config['cutoff_radius'], (int, float)):
            raise ConfigError("CUTOFF_RADIUS must be a number.")
        if not self._config['zenodo_url'].startswith(('http://', 'https://')):
            raise ConfigError("ZENODO_URL must be a valid HTTP URL.")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    @property
    def cutoff_radius(self) -> float:
        return self._config['cutoff_radius']

    @property
    def zenodo_url(self) -> str:
        return self._config['zenodo_url']

    @property
    def data_dir(self) -> Path:
        return self._config['data_dir']

    @property
    def processed_dir(self) -> Path:
        return self._config['processed_dir']

    @property
    def raw_dir(self) -> Path:
        return self._config['raw_dir']

    @property
    def log_file_path(self) -> Path:
        return self._config['log_file']

    @property
    def log_level(self) -> int:
        level_str = self._config['log_level']
        return getattr(logging, level_str, logging.INFO)

# Global config instance
_config_instance: Optional[EnvironmentConfig] = None

def reload_config():
    """Force reload of configuration."""
    global _config_instance
    _config_instance = EnvironmentConfig()

def get_config() -> EnvironmentConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance

def get_cutoff_radius() -> float:
    """Get the cutoff radius from config."""
    return get_config().cutoff_radius

def get_zenodo_url() -> str:
    """Get the Zenodo URL from config."""
    return get_config().zenodo_url

def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_config().data_dir

def get_processed_dir() -> Path:
    """Get the processed data directory path."""
    return get_config().processed_dir

def get_log_file_path() -> Path:
    """Get the log file path."""
    return get_config().log_file_path

def get_log_level() -> int:
    """Get the log level."""
    return get_config().log_level

def main():
    """Test configuration loading."""
    config = get_config()
    print(f"Project Root: {config.data_dir}")
    print(f"Cutoff Radius: {config.cutoff_radius}")
    print(f"Zenodo URL: {config.zenodo_url}")
    print(f"Log File: {config.log_file_path}")

if __name__ == "__main__":
    main()
