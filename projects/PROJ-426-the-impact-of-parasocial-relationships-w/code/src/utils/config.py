"""
Environment configuration management for API keys and data paths.

This module provides a centralized way to load and access configuration
values from environment variables and a local configuration file.
It ensures that required API keys and data paths are available before
any data processing or API calls are made.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Project root is assumed to be the parent of 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE_PATH = PROJECT_ROOT / "config" / "config.json"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
DATA_VALIDATION_DIR = DATA_DIR / "validation"
DATA_LEXICONS_DIR = DATA_DIR / "lexicons"


class ConfigError(Exception):
    """Raised when a required configuration value is missing or invalid."""
    pass


class Config:
    """
    Manages configuration for the project.

    Loads settings from environment variables and an optional config.json file.
    Environment variables take precedence over file-based configuration.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Start with defaults or file-based config
        if CONFIG_FILE_PATH.exists():
            with open(CONFIG_FILE_PATH, 'r') as f:
                self._config = json.load(f)
        else:
            self._config = {}

        # Override with environment variables
        # Expected env vars:
        # PUSHSHIFT_API_KEY (if needed, though Pushshift is often public now, sometimes keys are used for higher limits)
        # ZENODO_API_TOKEN (if needed for authenticated downloads, though often public)
        # DATA_PATH (optional override for base data directory)

        if 'PUSHSHIFT_API_KEY' in os.environ:
            self._config['pushshift_api_key'] = os.environ['PUSHSHIFT_API_KEY']

        if 'ZENODO_API_TOKEN' in os.environ:
            self._config['zenodo_api_token'] = os.environ['ZENODO_API_TOKEN']

        if 'DATA_PATH' in os.environ:
            data_path = Path(os.environ['DATA_PATH'])
            self._config['data_path'] = str(data_path)
            # Update internal directory references if base path is overridden
            global DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, DATA_VALIDATION_DIR, DATA_LEXICONS_DIR
            DATA_DIR = data_path
            DATA_RAW_DIR = DATA_DIR / "raw"
            DATA_PROCESSED_DIR = DATA_DIR / "processed"
            DATA_RESULTS_DIR = DATA_DIR / "results"
            DATA_VALIDATION_DIR = DATA_DIR / "validation"
            DATA_LEXICONS_DIR = DATA_DIR / "lexicons"

        # Ensure required directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create data directories if they don't exist."""
        directories = [
            DATA_RAW_DIR,
            DATA_PROCESSED_DIR,
            DATA_RESULTS_DIR,
            DATA_VALIDATION_DIR,
            DATA_LEXICONS_DIR
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key.
            default: Default value if key is not found.

        Returns:
            The configuration value or the default.
        """
        return self._config.get(key, default)

    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value.

        Args:
            key: The configuration key.

        Returns:
            The configuration value.

        Raises:
            ConfigError: If the key is missing.
        """
        if key not in self._config:
            raise ConfigError(f"Required configuration key '{key}' is missing. "
                              f"Please set it in config/config.json or as an environment variable.")
        return self._config[key]

    @property
    def data_dir(self) -> Path:
        """Get the base data directory."""
        return DATA_DIR

    @property
    def data_raw_dir(self) -> Path:
        """Get the raw data directory."""
        return DATA_RAW_DIR

    @property
    def data_processed_dir(self) -> Path:
        """Get the processed data directory."""
        return DATA_PROCESSED_DIR

    @property
    def data_results_dir(self) -> Path:
        """Get the results data directory."""
        return DATA_RESULTS_DIR

    @property
    def data_validation_dir(self) -> Path:
        """Get the validation data directory."""
        return DATA_VALIDATION_DIR

    @property
    def data_lexicons_dir(self) -> Path:
        """Get the lexicons data directory."""
        return DATA_LEXICONS_DIR

    @property
    def pushshift_api_key(self) -> Optional[str]:
        """Get the Pushshift API key if configured."""
        return self._config.get('pushshift_api_key')

    @property
    def zenodo_api_token(self) -> Optional[str]:
        """Get the Zenodo API token if configured."""
        return self._config.get('zenodo_api_token')


# Singleton instance for easy access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        The global Config instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config() -> Config:
    """
    Initialize or re-initialize the global configuration instance.

    Returns:
        The global Config instance.
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance