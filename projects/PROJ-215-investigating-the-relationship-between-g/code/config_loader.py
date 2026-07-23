import os
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import dotenv; if not present, the functions will raise ImportError
# when called, forcing the user to install python-dotenv if .env support is needed.
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from code.config import ensure_directories, get_output_path


def load_environment_variables(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file into os.environ.

    Args:
        env_path: Path to the .env file. If None, looks for .env in the
                  project root (parent of 'code' directory).

    Returns:
        True if loading was successful (or dotenv not available and no path
        was specified), False if the file was not found or dotenv is missing.

    Raises:
        ImportError: If a .env file path is provided but python-dotenv is not installed.
        FileNotFoundError: If the specified .env file does not exist.
    """
    if env_path:
        if not DOTENV_AVAILABLE:
            raise ImportError(
                "python-dotenv is required to load a specific .env file. "
                "Install it via 'pip install python-dotenv'."
            )
        env_file = Path(env_path)
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        return load_dotenv(str(env_file))
    else:
        # Default behavior: look for .env in project root
        if DOTENV_AVAILABLE:
            project_root = Path(__file__).resolve().parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                return load_dotenv(str(env_file))
        return True


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found.

    Returns:
        The value as a string, or the default if not found.
    """
    return os.getenv(key, default)


def get_int_config(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Retrieve an integer configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found or cannot be parsed.

    Returns:
        The value as an integer, or the default.
    """
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def get_float_config(key: str, default: Optional[float] = None) -> Optional[float]:
    """
    Retrieve a float configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found or cannot be parsed.

    Returns:
        The value as a float, or the default.
    """
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def get_bool_config(key: str, default: bool = False) -> bool:
    """
    Retrieve a boolean configuration value from environment variables.

    Args:
        key: The environment variable name.
        default: Default value if the key is not found.

    Returns:
        True if the value is 'true', '1', 'yes', 'on' (case-insensitive).
        False otherwise.
    """
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes', 'on')


def initialize_config() -> Dict[str, Any]:
    """
    Initialize the configuration by loading .env and ensuring directories exist.

    Returns:
        A dictionary containing configuration status and paths.
    """
    load_environment_variables()
    ensure_directories()
    
    return {
        "dotenv_available": DOTENV_AVAILABLE,
        "project_root": str(Path(__file__).resolve().parent.parent),
        "output_path": str(get_output_path()),
    }
