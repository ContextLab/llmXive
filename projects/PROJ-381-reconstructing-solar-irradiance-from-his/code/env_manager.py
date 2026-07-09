"""
Environment variable management for data paths.

This module provides utilities to load, validate, and retrieve
environment variables used for configuring data paths and other
project settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any


def load_env_vars(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.

    Args:
        env_file: Path to the .env file. If None, checks for '.env'
                  in the current working directory.

    Returns:
        Dictionary of loaded environment variables.
    """
    env_vars = {}
    if env_file is None:
        env_file = ".env"

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")

    return env_vars


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable value.

    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raises a ValueError if the variable is not set.

    Returns:
        The value of the environment variable or the default.

    Raises:
        ValueError: If the variable is required but not set.
    """
    # First check if it's already in os.environ
    value = os.environ.get(key)

    # If not found, try to load from .env file
    if value is None:
        env_vars = load_env_vars()
        value = env_vars.get(key)

    # If still not found, use default or raise error
    if value is None:
        if required:
            raise ValueError(f"Required environment variable '{key}' is not set.")
        return default

    return value


def get_data_path(path_name: str, relative_to: Optional[Path] = None) -> Path:
    """
    Get a data path from an environment variable.

    Args:
        path_name: The name of the environment variable (without prefix).
                   The variable is expected to be named DATA_{path_name}.
        relative_to: If provided, the path is resolved relative to this directory.
                    Otherwise, it's resolved relative to the project root.

    Returns:
        A Path object pointing to the data directory.

    Raises:
        ValueError: If the environment variable is not set.
    """
    env_key = f"DATA_{path_name.upper()}"
    path_str = get_env_var(env_key, required=True)

    if relative_to:
        return relative_to / path_str
    else:
        return Path(path_str)


def validate_data_paths() -> bool:
    """
    Validate that all required data paths exist.

    Returns:
        True if all paths exist, False otherwise.
    """
    required_vars = [
        "RAW_DATA_DIR",
        "PROCESSED_DATA_DIR",
        "MODELS_DIR",
        "FIGURES_DIR"
    ]

    all_valid = True
    for var in required_vars:
        key = f"DATA_{var}"
        path_str = get_env_var(key)
        if path_str:
            path = Path(path_str)
            if not path.exists():
                print(f"Warning: Path does not exist: {path}")
                all_valid = False
        else:
            print(f"Warning: Environment variable {key} is not set.")
            all_valid = False

    return all_valid


def setup_environment(env_file: Optional[str] = None) -> None:
    """
    Load environment variables from .env file and set them in os.environ.

    Args:
        env_file: Path to the .env file.
    """
    env_vars = load_env_vars(env_file)
    for key, value in env_vars.items():
        os.environ[key] = value

    # Ensure data directories exist
    from config import ensure_directories
    ensure_directories()