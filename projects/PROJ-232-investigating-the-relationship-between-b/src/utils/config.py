"""
Environment configuration management for llmXive project.

Handles .env file loading, API key retrieval, and data path configuration.
Ensures all required environment variables are present before proceeding.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import python-dotenv; if not available, manual loading fallback
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None  # type: ignore


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class EnvironmentConfig:
    """
    Manages environment configuration loading and validation.

    Loads configuration from:
    1. System environment variables
    2. .env file in project root (if present)

    Required variables for this project:
    - OPENNEURO_API_KEY: API key for OpenNeuro dataset access
    - DATA_DIR: Base directory for data storage (defaults to ./data)
    - OUTPUT_DIR: Base directory for outputs (defaults to ./data/output)
    """

    # Required environment variables
    REQUIRED_VARS: tuple[str, ...] = (
        "OPENNEURO_API_KEY",
    )

    # Optional environment variables with defaults
    OPTIONAL_VARS: dict[str, Any] = {
        "DATA_DIR": "./data",
        "OUTPUT_DIR": "./data/output",
        "FIGURES_DIR": "./figures",
        "LOG_LEVEL": "INFO",
        "SEED": "42",
    }

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize configuration by loading from environment and .env file.

        Args:
            env_path: Optional path to .env file. If None, searches in
                     project root (current working directory).
        """
        self._config: Dict[str, str] = {}
        self._env_path: Optional[Path] = env_path

        # Load .env file if available
        self._load_env_file()

        # Load from system environment
        self._load_from_system_env()

        # Validate required variables
        self._validate_required()

        # Set defaults for optional variables
        self._set_defaults()

    def _load_env_file(self) -> None:
        """Load configuration from .env file if it exists."""
        if self._env_path is None:
            # Search for .env in current directory
            self._env_path = Path.cwd() / ".env"

        if not self._env_path.exists():
            # .env file not found - this is okay, we'll use system env
            return

        if DOTENV_AVAILABLE and load_dotenv:
            load_dotenv(self._env_path, override=True)
        else:
            # Fallback: manual parsing of .env file
            self._manual_load_env_file()

    def _manual_load_env_file(self) -> None:
        """Manually parse .env file if python-dotenv is not available."""
        if not self._env_path or not self._env_path.exists():
            return

        with open(self._env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value

    def _load_from_system_env(self) -> None:
        """Load all environment variables into internal config."""
        for key in os.environ:
            self._config[key] = os.environ[key]

    def _validate_required(self) -> None:
        """Validate that all required environment variables are set."""
        missing = []
        for var in self.REQUIRED_VARS:
            if var not in self._config or not self._config[var]:
                missing.append(var)

        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please set them in your .env file or system environment."
            )

    def _set_defaults(self) -> None:
        """Set default values for optional environment variables."""
        for key, default in self.OPTIONAL_VARS.items():
            if key not in self._config:
                self._config[key] = str(default)

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a configuration value.

        Args:
            key: Environment variable name
            default: Default value if key not found (optional)

        Returns:
            Configuration value as string

        Raises:
            ConfigError: If required variable is missing and no default provided
        """
        if key in self._config:
            return self._config[key]
        if default is not None:
            return default
        raise ConfigError(f"Configuration key '{key}' not found")

    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get configuration value as integer."""
        value = self.get(key, str(default) if default is not None else "0")
        try:
            return int(value)
        except ValueError:
            raise ConfigError(f"Configuration key '{key}' must be an integer")

    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get configuration value as float."""
        value = self.get(key, str(default) if default is not None else "0.0")
        try:
            return float(value)
        except ValueError:
            raise ConfigError(f"Configuration key '{key}' must be a float")

    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """Get configuration value as Path object."""
        value = self.get(key, default)
        return Path(value).resolve()

    @property
    def openneuro_api_key(self) -> str:
        """Get OpenNeuro API key."""
        return self.get("OPENNEURO_API_KEY")

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self.get_path("DATA_DIR")

    @property
    def output_dir(self) -> Path:
        """Get output directory path."""
        return self.get_path("OUTPUT_DIR")

    @property
    def figures_dir(self) -> Path:
        """Get figures directory path."""
        return self.get_path("FIGURES_DIR")

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get("LOG_LEVEL", "INFO")

    @property
    def seed(self) -> int:
        """Get random seed."""
        return self.get_int("SEED", 42)

    def ensure_directories(self) -> None:
        """Create all configured directories if they don't exist."""
        for path in [self.data_dir, self.output_dir, self.figures_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, str]:
        """Return configuration as dictionary (without secrets)."""
        result = {}
        for key, value in self._config.items():
            if key.endswith("_KEY") or key.endswith("_SECRET"):
                result[key] = "***"  # Mask sensitive values
            else:
                result[key] = value
        return result

    def __repr__(self) -> str:
        return f"EnvironmentConfig(data_dir={self.data_dir}, output_dir={self.output_dir})"


# Global configuration instance
_config_instance: Optional[EnvironmentConfig] = None


def get_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Get or create the global configuration instance.

    Args:
        env_path: Optional path to .env file

    Returns:
        EnvironmentConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig(env_path)
    return _config_instance


def reload_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Force reload of configuration.

    Args:
        env_path: Optional path to .env file

    Returns:
        New EnvironmentConfig instance
    """
    global _config_instance
    _config_instance = EnvironmentConfig(env_path)
    return _config_instance
