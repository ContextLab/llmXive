import os
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import dotenv, but make it optional so the module loads even if not installed
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    load_dotenv = None  # type: ignore

from code.config import ensure_directories, get_output_path

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


def load_environment_variables(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.

    Args:
        env_path: Path to the .env file. Defaults to PROJECT_ROOT/.env

    Returns:
        bool: True if variables were loaded successfully, False otherwise.
    """
    target_path = env_path or ENV_FILE_PATH

    if not target_path.exists():
        # No .env file found; this is not an error, just a no-op
        return False

    if not HAS_DOTENV:
        # dotenv is not installed; try to manually parse the file
        _manual_load_env(target_path)
        return True

    return bool(load_dotenv(dotenv_path=target_path, override=False))


def _manual_load_env(env_path: Path) -> None:
    """
    Manually parse a .env file and set environment variables.
    This is a fallback when python-dotenv is not installed.

    Supports lines like: KEY=value, KEY="value", KEY='value'
    Ignores comments (lines starting with #) and empty lines.
    """
    if not env_path.exists():
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Remove surrounding quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            os.environ[key] = value


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found.

    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(key, default)


def get_int_config(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Retrieve an integer configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found or cannot be parsed.

    Returns:
        The integer value or the default.
    """
    val_str = os.getenv(key)
    if val_str is None:
        return default
    try:
        return int(val_str)
    except ValueError:
        return default


def get_float_config(key: str, default: Optional[float] = None) -> Optional[float]:
    """
    Retrieve a float configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found or cannot be parsed.

    Returns:
        The float value or the default.
    """
    val_str = os.getenv(key)
    if val_str is None:
        return default
    try:
        return float(val_str)
    except ValueError:
        return default


def get_bool_config(key: str, default: bool = False) -> bool:
    """
    Retrieve a boolean configuration value from environment variables.

    Accepts: 'true', '1', 'yes', 'on' (case-insensitive) as True.
    Everything else is False.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found.

    Returns:
        The boolean value or the default.
    """
    val_str = os.getenv(key)
    if val_str is None:
        return default
    return val_str.lower() in ("true", "1", "yes", "on")


def initialize_config() -> Dict[str, Any]:
    """
    Initialize the configuration by loading .env and ensuring directories exist.

    Returns:
        A dictionary containing the loaded configuration state.
    """
    loaded = load_environment_variables()
    ensure_directories()

    return {
        "env_loaded": loaded,
        "env_file_path": str(ENV_FILE_PATH),
        "project_root": str(PROJECT_ROOT),
        "dotenv_available": HAS_DOTENV,
    }
