"""
Environment configuration management for llmXive project.
Handles .env file loading, API key validation, and environment setup.
"""
import os
from pathlib import Path
from typing import List, Optional
import logging

from dotenv import load_dotenv

from .logging_config import get_logger

logger = get_logger(__name__)

ENV_FILE_PATH = Path(".env")
REQUIRED_KEYS: List[str] = []  # No API keys required for this specific project yet, but framework is ready

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. Defaults to project root .env.

    Returns:
        True if the file was found and loaded successfully, False otherwise.
    """
    target_path = env_path if env_path else ENV_FILE_PATH

    if not target_path.exists():
        logger.warning(f"Environment file not found at {target_path}. "
                       "Proceeding with system environment variables only.")
        return False

    try:
        loaded = load_dotenv(target_path, override=True)
        if loaded:
            logger.info(f"Successfully loaded environment variables from {target_path}")
        else:
            logger.warning(f"No variables loaded from {target_path} (file might be empty)")
        return loaded
    except Exception as e:
        logger.error(f"Failed to load environment file {target_path}: {e}")
        return False

def validate_api_keys(required_keys: Optional[List[str]] = None) -> List[str]:
    """
    Validate that all required API keys are present in the environment.

    Args:
        required_keys: List of environment variable names that must be set.
                       Defaults to REQUIRED_KEYS constant.

    Returns:
        List of missing key names. Empty list if all keys are present.
    """
    keys_to_check = required_keys if required_keys else REQUIRED_KEYS
    missing = []

    for key in keys_to_check:
        if not os.getenv(key):
            missing.append(key)
            logger.warning(f"Missing required environment variable: {key}")

    if missing:
        logger.error(f"Missing API keys: {', '.join(missing)}. "
                     "Please set them in your .env file or system environment.")
    else:
        logger.info("All required API keys are present.")

    return missing

def setup_environment(env_path: Optional[Path] = None,
                      validate: bool = True,
                      required_keys: Optional[List[str]] = None) -> bool:
    """
    Main entry point for setting up the environment.

    This function:
    1. Loads the .env file from the specified path (or default).
    2. Validates that all required API keys are present.

    Args:
        env_path: Optional path to the .env file.
        validate: If True, validate required keys after loading.
        required_keys: Optional list of keys to validate (overrides default).

    Returns:
        True if setup was successful (file loaded and keys valid if required).
        False if file loading failed or validation failed.
    """
    logger.info("Starting environment setup...")

    # Load .env file
    loaded = load_dotenv_file(env_path)

    # Validate keys if requested
    if validate:
        missing = validate_api_keys(required_keys)
        if missing:
            logger.error("Environment setup failed due to missing API keys.")
            return False

    logger.info("Environment setup completed successfully.")
    return True
