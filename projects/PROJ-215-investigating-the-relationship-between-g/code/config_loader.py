import os
from pathlib import Path
from typing import Optional, Dict, Any
from code.config import ensure_directories, get_output_path
from utils.logging import get_logger

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

def load_environment_variables(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file if it exists.
    If the file is not found, the function simply does nothing (no error raised).
    """
    if not DOTENV_AVAILABLE:
        logger = get_logger()
        logger.warning("python-dotenv is not installed. Environment variables from .env will not be loaded.")
        return

    if env_path is None:
        # Look for .env in the project root
        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / ".env"
    else:
        env_file = Path(env_path)

    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        logger = get_logger()
        logger.info(f"Loaded environment variables from {env_file}")
    else:
        logger = get_logger()
        logger.info(f"No .env file found at {env_file}. Using system environment variables.")

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a configuration value from environment variables.
    Falls back to the provided default if the key is not set.
    """
    return os.getenv(key, default)

def get_int_config(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Retrieve an integer configuration value from environment variables.
    Raises ValueError if the value cannot be converted to int.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' must be an integer, got '{value}'")

def get_float_config(key: str, default: Optional[float] = None) -> Optional[float]:
    """
    Retrieve a float configuration value from environment variables.
    Raises ValueError if the value cannot be converted to float.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' must be a float, got '{value}'")

def get_bool_config(key: str, default: bool = False) -> bool:
    """
    Retrieve a boolean configuration value from environment variables.
    Accepts common boolean string representations: 'true', '1', 'yes', 'on' -> True
    'false', '0', 'no', 'off' -> False
    """
    value = os.getenv(key)
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value

    true_values = {'true', '1', 'yes', 'on', 'enabled'}
    false_values = {'false', '0', 'no', 'off', 'disabled'}

    val_lower = value.lower().strip()
    
    if val_lower in true_values:
        return True
    elif val_lower in false_values:
        return False
    else:
        raise ValueError(f"Environment variable '{key}' has an invalid boolean value: '{value}'")

def initialize_config() -> Dict[str, Any]:
    """
    Main entry point to initialize the configuration system.
    1. Loads environment variables from .env if available.
    2. Ensures necessary directories exist.
    3. Returns a dictionary of key configuration values.
    """
    # Load environment variables
    load_environment_variables()

    # Ensure directories
    ensure_directories()

    logger = get_logger()
    logger.info("Configuration initialized successfully.")

    # Return a sample config dict that can be extended
    config = {
        "data_dir": get_output_path("data"),
        "results_dir": get_output_path("results"),
        "random_seed": get_int_config("RANDOM_SEEED", 42),
        "verbose": get_bool_config("VERBOSE", False),
    }

    return config
