"""
Environment variable management for dataset API keys and paths.

This module handles the loading, validation, and access of critical
environment variables required for the mindfulness training study,
specifically the OpenNeuro API key and the data directory path.
"""

import os
from typing import Optional


class EnvironmentError(Exception):
    """Custom exception for environment configuration errors."""
    pass


class EnvConfig:
    """
    Manages environment variable validation and access.

    Attributes:
        openneuro_api_key (str): The OpenNeuro API key.
        data_dir (str): The root directory for dataset storage.
    """

    # Required environment variable names
    OPENNEURO_API_KEY_VAR = "OPENNEURO_API_KEY"
    DATA_DIR_VAR = "DATA_DIR"

    def __init__(self) -> None:
        """
        Initialize and validate environment configuration.

        Raises:
            EnvironmentError: If any required variable is missing or empty.
        """
        self._validate_and_load()

    def _validate_and_load(self) -> None:
        """
        Validates that all required environment variables are present and non-empty.

        Raises:
            EnvironmentError: If validation fails.
        """
        missing_vars = []
        empty_vars = []

        # Check OPENNEURO_API_KEY
        api_key = os.getenv(self.OPENNEURO_API_KEY_VAR)
        if api_key is None:
            missing_vars.append(self.OPENNEURO_API_KEY_VAR)
        elif not api_key.strip():
            empty_vars.append(self.OPENNEURO_API_KEY_VAR)

        # Check DATA_DIR
        data_dir = os.getenv(self.DATA_DIR_VAR)
        if data_dir is None:
            missing_vars.append(self.DATA_DIR_VAR)
        elif not data_dir.strip():
            empty_vars.append(self.DATA_DIR_VAR)

        if missing_vars or empty_vars:
            error_msg_parts = []
            if missing_vars:
                error_msg_parts.append(
                    f"Missing required environment variables: {', '.join(missing_vars)}"
                )
            if empty_vars:
                error_msg_parts.append(
                    f"Environment variables are empty: {', '.join(empty_vars)}"
                )
            raise EnvironmentError("; ".join(error_msg_parts))

        # Store validated values
        self._openneuro_api_key = api_key.strip()
        self._data_dir = data_dir.strip()

    @property
    def openneuro_api_key(self) -> str:
        """Returns the validated OpenNeuro API key."""
        return self._openneuro_api_key

    @property
    def data_dir(self) -> str:
        """Returns the validated data directory path."""
        return self._data_dir

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the configuration.

        Note: Sensitive keys are masked in the output for safety.
        """
        return {
            "openneuro_api_key": "****" if self._openneuro_api_key else None,
            "data_dir": self._data_dir,
        }


# Singleton instance for global access
_config_instance: Optional[EnvConfig] = None


def get_config() -> EnvConfig:
    """
    Returns the singleton EnvConfig instance.

    Raises:
        EnvironmentError: If the environment has not been validated yet.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig()
    return _config_instance


def get_openneuro_api_key() -> str:
    """
    Convenience function to get the OpenNeuro API key.

    Returns:
        str: The API key.
    """
    return get_config().openneuro_api_key


def get_data_dir() -> str:
    """
    Convenience function to get the data directory path.

    Returns:
        str: The data directory path.
    """
    return get_config().data_dir
