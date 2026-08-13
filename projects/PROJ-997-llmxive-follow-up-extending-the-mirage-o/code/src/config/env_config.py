"""
Environment configuration loader for llmXive pipeline.

Provides strict loading of environment variables from .env files
with no synthetic fallbacks. Fails loudly if required variables are missing.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Default .env file path relative to project root
DEFAULT_ENV_PATH = Path(".env")

# Required environment variables for the pipeline
REQUIRED_VARS = [
    "MODEL_PATH",
    "DATASET_ID"
]


def load_config(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load configuration from a .env file.
    
    This function reads a .env file, parses key-value pairs, and loads them
    into the environment. It strictly enforces the presence of required variables.
    
    Args:
        env_path: Path to the .env file. If None, defaults to ./.env in the
                  current working directory.
    
    Returns:
        Dict[str, str]: A dictionary containing all loaded environment variables.
    
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
        ValueError: If any required environment variable is missing from the file
                    or the current environment.
    """
    if env_path is None:
        env_path = DEFAULT_ENV_PATH.resolve()
    
    # Check if the file exists
    if not env_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {env_path}")
    
    config = {}
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse key=value pairs
            if "=" not in line:
                logger.warning(f"Skipping malformed line {line_num} in {env_path}: {line}")
                continue
            
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            
            # Remove surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            
            if key:
                config[key] = value
                # Also set in os.environ for broader availability
                os.environ[key] = value
    
    # Validate required variables
    missing_vars = []
    for var in REQUIRED_VARS:
        if var not in config:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables in {env_path}: {missing_vars}. "
            f"Please ensure {env_path} contains entries for: {REQUIRED_VARS}"
        )
    
    logger.info(f"Successfully loaded configuration from {env_path}")
    logger.info(f"Loaded {len(config)} configuration variables")
    
    return config


def get_model_path() -> str:
    """
    Retrieve the MODEL_PATH from the loaded configuration.
    
    Returns:
        str: The path to the model.
    
    Raises:
        ValueError: If MODEL_PATH is not set.
    """
    value = os.environ.get("MODEL_PATH")
    if not value:
        raise ValueError("MODEL_PATH environment variable is not set.")
    return value


def get_dataset_id() -> str:
    """
    Retrieve the DATASET_ID from the loaded configuration.
    
    Returns:
        str: The dataset identifier.
    
    Raises:
        ValueError: If DATASET_ID is not set.
    """
    value = os.environ.get("DATASET_ID")
    if not value:
        raise ValueError("DATASET_ID environment variable is not set.")
    return value
