"""
Environment configuration management for the heat transport analysis pipeline.

Loads configuration values (cutoff_radius, zenodo_url, paths, etc.) from
environment variables or a .env file. Provides a centralized interface
to access these settings throughout the application.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load .env file if it exists
load_dotenv()

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Container for environment-based configuration values.
    
    Attributes:
        cutoff_radius (float): Cutoff radius in Angstroms for graph construction.
        zenodo_url (str): Base URL or specific record ID for Zenodo data.
        data_dir (Path): Root directory for raw data.
        processed_dir (Path): Root directory for processed data.
        log_file_path (Path): Path to the log file.
        log_level (str): Logging level (e.g., 'INFO', 'DEBUG').
    """
    
    def __init__(self):
        self.cutoff_radius: float = self._get_cutoff_radius()
        self.zenodo_url: str = self._get_zenodo_url()
        self.data_dir: Path = self._get_data_dir()
        self.processed_dir: Path = self._get_processed_dir()
        self.log_file_path: Path = self._get_log_file_path()
        self.log_level: str = self._get_log_level()
        
        # Validate critical configuration
        self._validate_config()

    def _get_cutoff_radius(self) -> float:
        """
        Retrieves the cutoff radius from environment variables.
        
        Returns:
            float: The cutoff radius in Angstroms.
        
        Raises:
            ConfigError: If the value is missing or invalid.
        """
        val = os.getenv('CUTOFF_RADIUS')
        if val is None:
            # Default fallback if not strictly required to fail, 
            # but per task spec we should load from env. 
            # We raise if missing to enforce configuration.
            raise ConfigError(
                "Environment variable 'CUTOFF_RADIUS' is not set. "
                "Please set it in your .env file or shell environment."
            )
        try:
            return float(val)
        except ValueError:
            raise ConfigError(
                f"Invalid CUTOFF_RADIUS value: '{val}'. Must be a float."
            )

    def _get_zenodo_url(self) -> str:
        """
        Retrieves the Zenodo URL from environment variables.
        
        Returns:
            str: The Zenodo URL or record ID.
        
        Raises:
            ConfigError: If the value is missing.
        """
        val = os.getenv('ZENODO_URL')
        if val is None:
            raise ConfigError(
                "Environment variable 'ZENODO_URL' is not set. "
                "Please set it in your .env file or shell environment."
            )
        return val

    def _get_data_dir(self) -> Path:
        """
        Retrieves the raw data directory path.
        
        Returns:
            Path: The path to the raw data directory.
        """
        val = os.getenv('DATA_DIR', 'data/raw')
        return Path(val).resolve()

    def _get_processed_dir(self) -> Path:
        """
        Retrieves the processed data directory path.
        
        Returns:
            Path: The path to the processed data directory.
        """
        val = os.getenv('PROCESSED_DIR', 'data/processed')
        return Path(val).resolve()

    def _get_log_file_path(self) -> Path:
        """
        Retrieves the log file path.
        
        Returns:
            Path: The path to the log file.
        """
        val = os.getenv('LOG_FILE_PATH', 'logs/analysis.log')
        return Path(val).resolve()

    def _get_log_level(self) -> str:
        """
        Retrieves the logging level.
        
        Returns:
            str: The logging level string.
        """
        val = os.getenv('LOG_LEVEL', 'INFO')
        return val.upper()

    def _validate_config(self) -> None:
        """
        Validates the loaded configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        if self.cutoff_radius <= 0:
            raise ConfigError(f"CUTOFF_RADIUS must be positive, got {self.cutoff_radius}")
        if not self.zenodo_url:
            raise ConfigError("ZENODO_URL cannot be empty")
        logger.info(f"Configuration loaded: cutoff_radius={self.cutoff_radius}, zenodo_url={self.zenodo_url}")

# Global configuration instance
_config: Optional[EnvironmentConfig] = None

def reload_config() -> EnvironmentConfig:
    """
    Forces a reload of the configuration from environment variables.
    
    Returns:
        EnvironmentConfig: The new configuration instance.
    """
    global _config
    _config = EnvironmentConfig()
    return _config

def get_config() -> EnvironmentConfig:
    """
    Gets the global configuration instance, initializing it if necessary.
    
    Returns:
        EnvironmentConfig: The configuration instance.
    """
    global _config
    if _config is None:
        _config = EnvironmentConfig()
    return _config

# Convenience getters for direct access
def get_cutoff_radius() -> float:
    """Returns the cutoff radius."""
    return get_config().cutoff_radius

def get_zenodo_url() -> str:
    """Returns the Zenodo URL."""
    return get_config().zenodo_url

def get_data_dir() -> Path:
    """Returns the raw data directory."""
    return get_config().data_dir

def get_processed_dir() -> Path:
    """Returns the processed data directory."""
    return get_config().processed_dir

def get_log_file_path() -> Path:
    """Returns the log file path."""
    return get_config().log_file_path

def get_log_level() -> str:
    """Returns the log level."""
    return get_config().log_level

def main():
    """
    CLI entry point to test configuration loading.
    """
    try:
        cfg = get_config()
        print("Configuration Loaded Successfully:")
        print(f"  Cutoff Radius: {cfg.cutoff_radius} Å")
        print(f"  Zenodo URL: {cfg.zenodo_url}")
        print(f"  Data Dir: {cfg.data_dir}")
        print(f"  Processed Dir: {cfg.processed_dir}")
        print(f"  Log File: {cfg.log_file_path}")
        print(f"  Log Level: {cfg.log_level}")
    except ConfigError as e:
        print(f"Configuration Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()