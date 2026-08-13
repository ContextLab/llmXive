"""
Environment variable management utilities for the llmXive OSM-UHI pipeline.

Provides functions to load .env files, retrieve API keys, and validate
required environment variables for Overpass API and AWS services.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

from config import get_path

# Initialize logger
logger = logging.getLogger(__name__)

def get_project_env_path() -> Path:
    """
    Returns the absolute path to the .env file in the project root.
    
    Returns:
        Path: Path to the .env file.
    """
    project_root = get_path("")  # get_path with empty string returns project root
    return project_root / ".env"

def load_env_vars(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Optional path to the .env file. If None, uses the project root .env.
    
    Returns:
        bool: True if loading was successful, False otherwise.
    """
    if env_path is None:
        env_path = get_project_env_path()
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Continuing without it.")
        return False
    
    try:
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable by key.
    
    Args:
        key: The environment variable key.
        default: Default value if the key is not set.
        required: If True, raises an error if the key is not set.
    
    Returns:
        Optional[str]: The value of the environment variable, or default.
    
    Raises:
        ValueError: If required=True and the key is not set.
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set.")
    
    if value is not None:
        logger.debug(f"Environment variable '{key}' retrieved.")
    
    return value

def get_overpass_api_key() -> Optional[str]:
    """
    Retrieve the Overpass API key from environment variables.
    
    Returns:
        Optional[str]: The Overpass API key, or None if not set.
    """
    return get_env_var("OVERPASS_API_KEY")

def get_aws_credentials() -> Dict[str, str]:
    """
    Retrieve AWS credentials from environment variables.
    
    Returns:
        Dict[str, str]: A dictionary containing 'aws_access_key_id', 
                        'aws_secret_access_key', and 'aws_region'.
    
    Raises:
        ValueError: If any required AWS credential is missing.
    """
    required_keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION"
    ]
    
    credentials = {}
    missing_keys = []
    
    for key in required_keys:
        value = get_env_var(key)
        if value:
            credentials[key] = value
        else:
            missing_keys.append(key)
    
    if missing_keys:
        raise ValueError(f"Missing required AWS credentials: {', '.join(missing_keys)}")
    
    logger.info("AWS credentials loaded successfully.")
    return credentials

def validate_required_env_vars(required_vars: List[str]) -> bool:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of environment variable keys that must be set.
    
    Returns:
        bool: True if all required variables are set, False otherwise.
    """
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    logger.info("All required environment variables are set.")
    return True

def create_example_env_file(output_path: Optional[Path] = None) -> Path:
    """
    Create an example .env file with placeholder values for required keys.
    
    Args:
        output_path: Optional path to write the example file. Defaults to project root .env.example.
    
    Returns:
        Path: The path to the created example file.
    """
    if output_path is None:
        output_path = get_path(".env.example")
    
    example_content = """
# Overpass API Configuration
# Get your API key from: https://overpass-api.de/
OVERPASS_API_KEY=your_overpass_api_key_here

# AWS Configuration for MODIS/Landsat Data
# Get credentials from AWS IAM Console
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-west-2

# Optional: Custom Overpass Server URL
# OVERPASS_URL=https://overpass-api.de/api/interpreter
""".strip()
    
    try:
        with open(output_path, "w") as f:
            f.write(example_content)
        logger.info(f"Created example environment file at {output_path}")
    except Exception as e:
        logger.error(f"Failed to create example env file: {e}")
        raise
    
    return output_path

# Initialize environment on module import
load_env_vars()