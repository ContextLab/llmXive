"""
Environment variable management for API keys and configuration.
Handles loading from .env files and providing typed accessors.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = lambda *args, **kwargs: False  # type: ignore

from .logging import get_logger

logger = get_logger(__name__)

# Default path relative to project root
DEFAULT_ENV_PATH = Path(__file__).parent.parent.parent / ".env"


def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. Defaults to project root .env.

    Returns:
        bool: True if loaded successfully, False otherwise.
    """
    if env_path is None:
        env_path = DEFAULT_ENV_PATH

    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                       "Using system environment variables only.")
        return False

    if not DOTENV_AVAILABLE:
        logger.error("python-dotenv package is not installed. "
                     "Install it via `pip install python-dotenv` to use .env files.")
        return False

    try:
        loaded = load_dotenv(dotenv_path=env_path, override=False)
        if loaded:
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f"No variables loaded from {env_path} (already set or empty)")
        return loaded
    except Exception as e:
        logger.error(f"Failed to load environment from {env_path}: {e}")
        return False


def get_api_key(service_name: str, required: bool = True) -> Optional[str]:
    """
    Retrieve an API key for a specific service from environment variables.

    Expected environment variable format: {SERVICE_NAME}_API_KEY
    e.g., OVERPASS_API_KEY, AWS_ACCESS_KEY_ID (handled separately if needed)

    Args:
        service_name: The service name (e.g., 'OVERPASS', 'AWS').
        required: If True, raises a ValueError if the key is missing.

    Returns:
        The API key string or None if not found and not required.

    Raises:
        ValueError: If the key is required but not found.
    """
    env_var_name = f"{service_name.upper()}_API_KEY"
    key = os.getenv(env_var_name)

    if key is None:
        if required:
            # Check if it's a known service that might use a different var name
            if service_name.upper() == "AWS":
                # AWS often uses specific vars, but we stick to convention or fallback
                key = os.getenv("AWS_ACCESS_KEY_ID")
                if key:
                    return key
            
            raise ValueError(
                f"Required API key '{env_var_name}' not found in environment. "
                f"Please set it in your .env file or system environment."
            )
        return None
    
    return key


def get_config_value(key: str, default: Any = None, cast_type: type = str) -> Any:
    """
    Retrieve a generic configuration value with type casting.

    Args:
        key: The environment variable name.
        default: Default value if key is missing.
        cast_type: Type to cast the value to (str, int, float, bool).

    Returns:
        The value cast to the requested type, or the default.
    """
    raw_value = os.getenv(key)
    if raw_value is None:
        return default

    if cast_type == bool:
        # Handle string representations of booleans
        if raw_value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif raw_value.lower() in ('false', '0', 'no', 'off'):
            return False
        return default
    
    try:
        return cast_type(raw_value)
    except ValueError:
        logger.warning(f"Could not cast '{raw_value}' to {cast_type.__name__} for key '{key}'. Using default.")
        return default


def validate_required_keys(services: list) -> bool:
    """
    Validate that API keys for a list of services are present.

    Args:
        services: List of service names (e.g., ['OVERPASS', 'AWS']).

    Returns:
        bool: True if all keys are present, False otherwise.
    """
    missing = []
    for service in services:
        key = os.getenv(f"{service.upper()}_API_KEY")
        if service.upper() == "AWS" and not key:
            key = os.getenv("AWS_ACCESS_KEY_ID")
        
        if not key:
            missing.append(service)

    if missing:
        logger.error(f"Missing required API keys for: {', '.join(missing)}")
        return False
    
    logger.info("All required API keys are present.")
    return True
