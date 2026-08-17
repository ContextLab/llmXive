"""
Environment configuration management module.
Handles loading of .env files and accessing configuration variables.
"""
import os
from pathlib import Path
from typing import Optional, Any
import dotenv

# Load .env file from the project root
# The project root is assumed to be the parent of 'src'
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / "config" / ".env"

# Load environment variables if .env exists
if env_path.exists():
    dotenv.load_dotenv(env_path)
else:
    # If .env doesn't exist, try to load from root (fallback)
    root_env_path = project_root / ".env"
    if root_env_path.exists():
        dotenv.load_dotenv(root_env_path)
    else:
        # If no .env found, we proceed with system environment variables
        pass


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def get_env_variable(name: str, default: Optional[Any] = None, required: bool = False) -> Any:
    """
    Retrieve an environment variable.

    Args:
        name: The name of the environment variable.
        default: Default value if the variable is not set.
        required: If True, raise ConfigError if the variable is missing.

    Returns:
        The value of the environment variable or the default.

    Raises:
        ConfigError: If the variable is required but not set.
    """
    value = os.getenv(name, default)

    if required and value is None:
        raise ConfigError(f"Required environment variable '{name}' is not set.")

    return value


def get_data_path(subdir: Optional[str] = None) -> Path:
    """
    Get the base data directory path.

    Args:
        subdir: Optional subdirectory name (raw, processed, derived).

    Returns:
        Path object pointing to the data directory.
    """
    base_path = Path(get_env_variable("DATA_ROOT", "data"))
    if subdir:
        return base_path / subdir
    return base_path


def get_config_path() -> Path:
    """
    Get the config directory path.

    Returns:
        Path object pointing to the config directory.
    """
    return Path(get_env_variable("CONFIG_PATH", "config"))


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.

    Returns:
        True if DEBUG_MODE is set to 'true' (case-insensitive), False otherwise.
    """
    return get_env_variable("DEBUG_MODE", "false").lower() == "true"


def use_real_data_only() -> bool:
    """
    Check if the system should use real data only.

    Returns:
        True if USE_REAL_DATA_ONLY is set to 'true', False otherwise.
    """
    return get_env_variable("USE_REAL_DATA_ONLY", "true").lower() == "true"
