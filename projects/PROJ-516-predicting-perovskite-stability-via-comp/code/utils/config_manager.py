"""
Environment configuration management for API keys and project settings.

This module handles loading .env files, retrieving API keys, and validating
that required environment variables are present.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback if python-dotenv is not installed, though it should be in requirements
    def load_dotenv(path: Optional[Path] = None) -> bool:
        logging.warning("python-dotenv not installed. Environment variables must be set in the shell.")
        return False

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_dotenv_file(project_root: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        project_root: The root directory of the project. Defaults to the
                      directory containing this module.

    Returns:
        bool: True if the file was loaded successfully, False otherwise.
    """
    if project_root is None:
        # Default to the directory containing this file
        project_root = Path(__file__).resolve().parent.parent

    env_path = project_root / ".env"

    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                       "Please create one based on .env.example.")
        return False

    logger.info(f"Loading environment variables from {env_path}")
    return load_dotenv(dotenv_path=env_path)


def get_api_key(service: str) -> str:
    """
    Retrieve an API key for a specific service.

    Args:
        service: The name of the service (e.g., 'MATERIALS_PROJECT', 'NREL').

    Returns:
        str: The API key.

    Raises:
        ConfigError: If the API key is not found in the environment.
    """
    env_var_map = {
        "MATERIALS_PROJECT": "MATERIALS_PROJECT_API_KEY",
        "MP": "MATERIALS_PROJECT_API_KEY",
        "NREL": "NREL_API_KEY",
    }

    env_var = env_var_map.get(service.upper())
    if not env_var:
        raise ConfigError(f"Unknown service: {service}. Available: {list(env_var_map.keys())}")

    key = os.getenv(env_var)
    if not key:
        raise ConfigError(
            f"API key for '{service}' not found. "
            f"Set the '{env_var}' environment variable or add it to .env file."
        )

    return key


def validate_environment(required_services: Optional[list] = None) -> Dict[str, bool]:
    """
    Validate that required environment variables are present.

    Args:
        required_services: List of service names to check. Defaults to
                           ['MATERIALS_PROJECT'].

    Returns:
        Dict[str, bool]: A dictionary mapping service names to their validation status.
    """
    if required_services is None:
        required_services = ["MATERIALS_PROJECT"]

    results = {}
    for service in required_services:
        try:
            get_api_key(service)
            results[service] = True
        except ConfigError as e:
            results[service] = False
            logger.error(str(e))

    return results
