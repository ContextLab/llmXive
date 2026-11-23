"""
Environment Configuration Management Module.

This module provides a robust way to manage environment variables,
API keys, and data paths for the research pipeline. It loads configuration
from a .env file (if present) and validates required variables.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Attempt to import dotenv, but make it optional for environments where it's not installed
try:
    from dotenv import load_dotenv, find_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    # Fallback: load_dotenv will be a no-op function
    def load_dotenv(path=None):
        return False

from .config import Config, ConfigError, get_config, init_config as init_base_config

class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

class EnvConfig(Config):
    """
    Specialized configuration class for environment variables and paths.
    Extends the base Config class to handle .env file loading and validation.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize the environment configuration.

        Args:
            env_path: Optional path to a specific .env file. If None,
                      searches for .env in the current directory and parent directories.
        """
        super().__init__()
        self._env_path = env_path
        self._load_environment()
        self._validate_required()

    def _load_environment(self):
        """Load environment variables from .env file if available."""
        if HAS_DOTENV:
            if self._env_path:
                if not self._env_path.exists():
                    logging.warning(f"Specified .env file not found: {self._env_path}")
                    return
                load_dotenv(self._env_path)
            else:
                # Try to find .env in current directory or project root
                dotenv_path = find_dotenv()
                if dotenv_path:
                    load_dotenv(dotenv_path)
                else:
                    logging.debug("No .env file found. Using system environment variables.")
        else:
            logging.warning("python-dotenv not installed. Using only system environment variables.")

    def _validate_required(self):
        """
        Validate that required environment variables are present.
        Raises EnvConfigError if any are missing.
        """
        # Define required variables based on project needs
        required_vars = [
            "DATA_ROOT_DIR",
            "DATA_RAW_DIR",
            "DATA_PROCESSED_DIR",
            "DATA_RESULTS_DIR",
            "DATA_VALIDATION_DIR",
            "DATA_LEXICONS_DIR"
        ]

        missing = []
        for var in required_vars:
            if var not in os.environ:
                missing.append(var)

        if missing:
            raise EnvConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please create a .env file based on config/.env.example and fill in the values."
            )

        # Validate path existence (create if necessary)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all configured data directories exist."""
        dirs_to_create = [
            "DATA_ROOT_DIR",
            "DATA_RAW_DIR",
            "DATA_PROCESSED_DIR",
            "DATA_RESULTS_DIR",
            "DATA_VALIDATION_DIR",
            "DATA_LEXICONS_DIR",
            "LOG_FILE" # Handle log directory
        ]

        for var in dirs_to_create:
            if var in os.environ:
                path_str = os.environ[var]
                # Handle log file path (extract directory)
                if var == "LOG_FILE":
                    path_str = str(Path(path_str).parent)

                path = Path(path_str)
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        logging.info(f"Created directory: {path}")
                    except OSError as e:
                        raise EnvConfigError(f"Failed to create directory {path}: {e}")

    def get_path(self, var_name: str, default: Optional[str] = None) -> Path:
        """
        Get an environment variable as a Path object.

        Args:
            var_name: Name of the environment variable.
            default: Optional default value if variable is not set.

        Returns:
            Path object pointing to the directory/file.

        Raises:
            EnvConfigError: If variable is required but missing and no default provided.
        """
        value = os.environ.get(var_name, default)
        if value is None:
            raise EnvConfigError(f"Required environment variable '{var_name}' is not set.")
        return Path(value)

    def get_api_key(self, var_name: str, required: bool = True) -> Optional[str]:
        """
        Get an API key from environment variables.

        Args:
            var_name: Name of the environment variable.
            required: If True, raises error if missing.

        Returns:
            The API key string, or None if not required and missing.

        Raises:
            EnvConfigError: If required and missing.
        """
        value = os.environ.get(var_name)
        if value is None and required:
            raise EnvConfigError(f"Required API key '{var_name}' is not set.")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Export current configuration to a dictionary (excluding sensitive keys)."""
        sensitive_prefixes = ["API_KEY", "TOKEN", "SECRET", "PASSWORD"]
        result = {}
        for key in os.environ:
            if any(key.startswith(prefix) for prefix in sensitive_prefixes):
                continue
            result[key] = os.environ[key]
        return result


_env_config_instance: Optional[EnvConfig] = None

def init_env_config(env_path: Optional[Path] = None) -> EnvConfig:
    """
    Initialize the global environment configuration singleton.

    Args:
        env_path: Optional path to .env file.

    Returns:
        The initialized EnvConfig instance.
    """
    global _env_config_instance
    if _env_config_instance is None:
        _env_config_instance = EnvConfig(env_path)
    return _env_config_instance

def get_env_config() -> EnvConfig:
    """
    Get the global environment configuration instance.

    Returns:
        The EnvConfig instance.

    Raises:
        EnvConfigError: If not yet initialized.
    """
    if _env_config_instance is None:
        raise EnvConfigError("Environment configuration not initialized. Call init_env_config() first.")
    return _env_config_instance

def setup_environment_from_file(env_path: Path) -> EnvConfig:
    """
    Convenience function to setup environment from a specific .env file.

    Args:
        env_path: Path to the .env file.

    Returns:
        The initialized EnvConfig instance.
    """
    return init_env_config(env_path)

def validate_and_setup_environment() -> Dict[str, Any]:
    """
    Validate environment setup and return a summary report.

    Returns:
        Dictionary with validation status and summary of paths.
    """
    config = get_env_config()
    
    paths = {
        "data_root": str(config.get_path("DATA_ROOT_DIR")),
        "data_raw": str(config.get_path("DATA_RAW_DIR")),
        "data_processed": str(config.get_path("DATA_PROCESSED_DIR")),
        "data_results": str(config.get_path("DATA_RESULTS_DIR")),
        "data_validation": str(config.get_path("DATA_VALIDATION_DIR")),
        "data_lexicons": str(config.get_path("DATA_LEXICONS_DIR")),
    }

    # Check API keys (without exposing values)
    api_keys_status = {}
    api_vars = ["PUSHSHIFT_API_KEY", "ZENODO_API_TOKEN"]
    for var in api_vars:
        if os.environ.get(var):
            api_keys_status[var] = "SET"
        else:
            api_keys_status[var] = "MISSING"

    return {
        "status": "SUCCESS",
        "paths": paths,
        "api_keys_status": api_keys_status,
        "dotenv_available": HAS_DOTENV
    }
