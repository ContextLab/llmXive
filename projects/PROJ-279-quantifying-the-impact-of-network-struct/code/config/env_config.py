"""
Environment configuration management.

Loads configuration from environment variables with sensible defaults.
Implements Constitution Principle IV: Configuration reproducibility.
"""
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
    """Environment configuration container."""
    
    def __init__(self):
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            'cutoff_radius': float(os.getenv('CUTOFF_RADIUS', '3.0')),
            'zenodo_url': os.getenv('ZENODO_URL', 'https://zenodo.org/api/records'),
            'data_dir': os.getenv('DATA_DIR', 'data'),
            'processed_dir': os.getenv('PROCESSED_DIR', 'data/processed'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file_path': os.getenv('LOG_FILE_PATH', 'logs/analysis.log'),
            'max_workers': int(os.getenv('MAX_WORKERS', '4')),
            'timeout_seconds': int(os.getenv('TIMEOUT_SECONDS', '3600')),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def get_cutoff_radius(self) -> float:
        """Get cutoff radius for graph construction."""
        return self._config['cutoff_radius']
    
    def get_zenodo_url(self) -> str:
        """Get Zenodo API URL."""
        return self._config['zenodo_url']
    
    def get_data_dir(self) -> Path:
        """Get base data directory."""
        return Path(self._config['data_dir'])
    
    def get_processed_dir(self) -> Path:
        """Get processed data directory."""
        return Path(self._config['processed_dir'])
    
    def get_log_level(self) -> str:
        """Get logging level."""
        return self._config['log_level']
    
    def get_log_file_path(self) -> Path:
        """Get log file path."""
        return Path(self._config['log_file_path'])

# Global configuration instance
_config_instance: Optional[EnvironmentConfig] = None

def get_config() -> EnvironmentConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance

def reload_config() -> EnvironmentConfig:
    """Reload configuration from environment variables."""
    global _config_instance
    _config_instance = EnvironmentConfig()
    return _config_instance

def get_cutoff_radius() -> float:
    """Get cutoff radius from global config."""
    return get_config().get_cutoff_radius()

def get_zenodo_url() -> str:
    """Get Zenodo URL from global config."""
    return get_config().get_zenodo_url()

def get_data_dir() -> Path:
    """Get data directory from global config."""
    return get_config().get_data_dir()

def get_processed_dir() -> Path:
    """Get processed directory from global config."""
    return get_config().get_processed_dir()

def get_log_level() -> str:
    """Get log level from global config."""
    return get_config().get_log_level()

def get_log_file_path() -> Path:
    """Get log file path from global config."""
    return get_config().get_log_file_path()

def main():
    """
    Main entry point for configuration demonstration.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Current configuration:")
    logger.info(f"  Cutoff Radius: {get_cutoff_radius()} Å")
    logger.info(f"  Zenodo URL: {get_zenodo_url()}")
    logger.info(f"  Data Directory: {get_data_dir()}")
    logger.info(f"  Processed Directory: {get_processed_dir()}")
    logger.info(f"  Log Level: {get_log_level()}")
    logger.info(f"  Log File: {get_log_file_path()}")

if __name__ == "__main__":
    main()
