"""
Environment configuration management for the Early Life Stress project.

This module handles environment variable loading and provides a centralized
configuration access point. It supports optional .env file loading while
defaulting to relative paths as defined in code/config.py.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import python-dotenv if available, otherwise provide a no-op loader
try:
    import dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    dotenv = None

from code.config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, CODE_DIR, TESTS_DIR, CONTRACTS_DIR


def load_environment(env_file: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.

    Args:
        env_file: Path to the .env file. If None, defaults to PROJECT_ROOT/.env

    Returns:
        True if a .env file was found and loaded, False otherwise.
    """
    if env_file is None:
        env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        return False

    if HAS_DOTENV:
        dotenv.load_dotenv(env_file)
        return True
    else:
        # Fallback: manual parsing if python-dotenv is not installed
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        return True


class EnvironmentConfig:
    """
    Centralized environment configuration manager.

    Provides access to environment variables with sensible defaults based on
    the project structure defined in code/config.py.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self._loaded = False
        self._config: Dict[str, Any] = {}

    def load(self, env_file: Optional[Path] = None) -> bool:
        """
        Load environment variables from .env file.

        Args:
            env_file: Optional path to .env file

        Returns:
            True if loaded successfully
        """
        if not self._loaded:
            self._loaded = load_environment(env_file)
        return self._loaded

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable value.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            The value or default
        """
        return os.environ.get(key, default)

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get an environment variable as an integer.

        Args:
            key: Environment variable name
            default: Default value if not found or invalid

        Returns:
            The integer value or default
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get an environment variable as a float.

        Args:
            key: Environment variable name
            default: Default value if not found or invalid

        Returns:
            The float value or default
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """
        Get an environment variable as a boolean.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            The boolean value or default
        """
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return PROJECT_ROOT

    @property
    def data_raw_dir(self) -> Path:
        """Get the raw data directory."""
        return DATA_RAW_DIR

    @property
    def data_processed_dir(self) -> Path:
        """Get the processed data directory."""
        return DATA_PROCESSED_DIR

    @property
    def code_dir(self) -> Path:
        """Get the code directory."""
        return CODE_DIR

    @property
    def tests_dir(self) -> Path:
        """Get the tests directory."""
        return TESTS_DIR

    @property
    def contracts_dir(self) -> Path:
        """Get the contracts directory."""
        return CONTRACTS_DIR

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as a dictionary.

        Returns:
            Dictionary of all configuration values
        """
        return {
            'project_root': str(self.project_root),
            'data_raw_dir': str(self.data_raw_dir),
            'data_processed_dir': str(self.data_processed_dir),
            'code_dir': str(self.code_dir),
            'tests_dir': str(self.tests_dir),
            'contracts_dir': str(self.contracts_dir),
            'dotenv_available': HAS_DOTENV,
            'environment_loaded': self._loaded,
        }


# Global instance
config = EnvironmentConfig()


def initialize_environment() -> bool:
    """
    Initialize the environment configuration.

    This function should be called at the start of the application to
    ensure all environment variables are loaded and paths are configured.

    Returns:
        True if initialization was successful
    """
    return config.load()


if __name__ == "__main__":
    # Test the environment configuration
    print("Initializing environment configuration...")
    success = initialize_environment()
    print(f"Environment loaded: {success}")
    print(f"Python-dotenv available: {HAS_DOTENV}")
    print(f"Project root: {config.project_root}")
    print(f"Data raw dir: {config.data_raw_dir}")
    print(f"Data processed dir: {config.data_processed_dir}")
    print(f"Code dir: {config.code_dir}")
    print(f"Tests dir: {config.tests_dir}")
    print(f"Contracts dir: {config.contracts_dir}")
    print("\nConfiguration dump:")
    print(json.dumps(config.to_dict(), indent=2))
