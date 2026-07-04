"""
Environment variable management for dataset API keys and project configuration.

This module handles the loading, validation, and access of environment variables
required for the project, specifically OPENNEURO_API_KEY and DATA_DIR.
"""
import os
from typing import Optional
from pathlib import Path


class EnvironmentError(Exception):
    """Custom exception for environment configuration errors."""
    pass


class EnvConfig:
    """
    Container for validated environment configuration.

    Attributes:
        openneuro_api_key (str): The API key for OpenNeuro access.
        data_dir (Path): The root directory for data storage.
    """

    def __init__(self, openneuro_api_key: str, data_dir: str):
        if not openneuro_api_key or not openneuro_api_key.strip():
            raise EnvironmentError("OPENNEURO_API_KEY must be a non-empty string.")
        
        if not data_dir or not data_dir.strip():
            raise EnvironmentError("DATA_DIR must be a non-empty string.")

        self.openneuro_api_key = openneuro_api_key.strip()
        self.data_dir = Path(data_dir).expanduser().resolve()

        if not self.data_dir.exists():
            # We allow the directory to not exist yet, as scripts may create it,
            # but we validate the path structure is valid.
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise EnvironmentError(f"DATA_DIR path '{data_dir}' is not writable.")
            except Exception as e:
                raise EnvironmentError(f"Invalid DATA_DIR path: {e}")

_config: Optional[EnvConfig] = None


def get_config() -> EnvConfig:
    """
    Retrieve or initialize the global environment configuration.

    Returns:
        EnvConfig: The validated configuration object.

    Raises:
        EnvironmentError: If required variables are missing or invalid.
    """
    global _config
    if _config is not None:
        return _config

    openneuro_key = os.getenv("OPENNEURO_API_KEY")
    data_dir = os.getenv("DATA_DIR")

    # Validation rules: required, non-empty
    if not openneuro_key:
        raise EnvironmentError(
            "Environment variable 'OPENNEURO_API_KEY' is required but not set."
        )
    
    if not data_dir:
        raise EnvironmentError(
            "Environment variable 'DATA_DIR' is required but not set."
        )

    _config = EnvConfig(openneuro_key, data_dir)
    return _config


def get_openneuro_api_key() -> str:
    """
    Get the OpenNeuro API key.

    Returns:
        str: The validated API key.

    Raises:
        EnvironmentError: If the key is not configured.
    """
    return get_config().openneuro_api_key


def get_data_dir() -> Path:
    """
    Get the data directory path.

    Returns:
        Path: The validated data directory path.

    Raises:
        EnvironmentError: If the directory is not configured.
    """
    return get_config().data_dir
