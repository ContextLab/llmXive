"""
Environment configuration management for the glass transition prediction project.

This module handles loading and validating the Zenodo DOI configuration from
a .env file. It ensures that critical environment variables are present before
attempting data fetch operations.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from utils import get_project_root, setup_logging

# Initialize logger
logger = setup_logging("config")

# Path to the .env file relative to project root
ENV_FILE_PATH = ".env"

# Required environment variable keys
REQUIRED_VARS = [
    "ZENODO_DOI",
    "ZENODO_API_URL",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR"
]

def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Optional path to the .env file. If None, defaults to
                  <project_root>/.env

    Returns:
        True if loading was successful and required variables are present.
        False if the file is missing or required variables are absent.

    Raises:
        FileNotFoundError: If the .env file does not exist at the specified path.
    """
    if env_path is None:
        env_path = get_project_root() / ENV_FILE_PATH

    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                       "Using system environment variables only.")
        return False

    loaded = load_dotenv(dotenv_path=env_path)
    if not loaded:
        logger.warning(f"Failed to load .env file from {env_path}")
        return False

    logger.info(f"Successfully loaded environment from {env_path}")
    return True

def get_zenodo_doi() -> str:
    """
    Retrieve the Zenodo DOI for the glass transition dataset.

    Returns:
        The DOI string.

    Raises:
        RuntimeError: If the ZENODO_DOI environment variable is not set.
    """
    doi = os.getenv("ZENODO_DOI")
    if not doi:
        raise RuntimeError(
            "ZENODO_DOI environment variable is not set. "
            "Please ensure it is defined in the .env file or system environment."
        )
    logger.debug(f"Retrieved Zenodo DOI: {doi}")
    return doi

def get_zenodo_api_url() -> str:
    """
    Retrieve the Zenodo API base URL.

    Returns:
        The API URL string. Defaults to https://zenodo.org/api if not set.

    Raises:
        RuntimeError: If the URL is explicitly set to an empty string.
    """
    url = os.getenv("ZENODO_API_URL", "https://zenodo.org/api")
    if not url:
        raise RuntimeError(
            "ZENODO_API_URL environment variable is empty. "
            "Please define a valid API URL in the .env file."
        )
    logger.debug(f"Retrieved Zenodo API URL: {url}")
    return url

def get_raw_data_dir() -> Path:
    """
    Retrieve the path for the raw data directory.

    Returns:
        Path object for the raw data directory.

    Raises:
        RuntimeError: If the path is not set or invalid.
    """
    path_str = os.getenv("RAW_DATA_DIR")
    if not path_str:
        raise RuntimeError(
            "RAW_DATA_DIR environment variable is not set. "
            "Please define the path in the .env file."
        )
    return Path(path_str)

def get_processed_data_dir() -> Path:
    """
    Retrieve the path for the processed data directory.

    Returns:
        Path object for the processed data directory.

    Raises:
        RuntimeError: If the path is not set or invalid.
    """
    path_str = os.getenv("PROCESSED_DATA_DIR")
    if not path_str:
        raise RuntimeError(
            "PROCESSED_DATA_DIR environment variable is not set. "
            "Please define the path in the .env file."
        )
    return Path(path_str)

def validate_configuration() -> bool:
    """
    Validate that all required environment variables are present and valid.

    Returns:
        True if configuration is valid.

    Raises:
        RuntimeError: If any required variable is missing or invalid.
    """
    missing = []
    for var in REQUIRED_VARS:
        if var not in os.environ or not os.environ[var]:
            missing.append(var)

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please update your .env file."
        )

    logger.info("Configuration validation successful.")
    return True

def initialize_config() -> dict:
    """
    Initialize and load the full configuration dictionary.

    This function attempts to load the .env file first, then validates
    and returns a dictionary of all configuration values.

    Returns:
        Dictionary containing configuration values:
        - doi: Zenodo DOI
        - api_url: Zenodo API URL
        - raw_data_dir: Path to raw data directory
        - processed_data_dir: Path to processed data directory

    Raises:
        RuntimeError: If configuration cannot be loaded or validated.
    """
    load_environment()
    
    try:
        config = {
            "doi": get_zenodo_doi(),
            "api_url": get_zenodo_api_url(),
            "raw_data_dir": str(get_raw_data_dir()),
            "processed_data_dir": str(get_processed_data_dir())
        }
        validate_configuration()
        return config
    except RuntimeError as e:
        logger.error(f"Configuration initialization failed: {e}")
        raise
