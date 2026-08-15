"""
Environment variable management utilities for the Urban Heat Island project.

Handles loading .env files, retrieving API keys (Overpass, AWS), and validation.
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
    """
    return get_path("") / ".env"

def load_env_vars(env_path: Optional[Path] = None) -> bool:
    """
    Loads environment variables from a .env file.
    
    Args:
        env_path: Optional explicit path to .env file. Defaults to project root.
        
    Returns:
        True if loading was successful (or file didn't exist but wasn't required),
        False if a required file was missing or loading failed.
    """
    if env_path is None:
        env_path = get_project_env_path()
    
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                       "Please create it or copy from .env.example.")
        return False
    
    try:
        # load_dotenv returns True if the file was found and loaded
        success = load_dotenv(dotenv_path=env_path, override=True)
        if success:
            logger.info(f"Environment variables loaded from {env_path}")
        else:
            logger.warning(f"Failed to load environment variables from {env_path}")
        return success
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        return False

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieves an environment variable.
    
    Args:
        key: The environment variable name.
        default: Default value if the key is not set.
        required: If True, raises an error if the key is missing.
        
    Returns:
        The value of the environment variable or the default.
        
    Raises:
        ValueError: If required=True and the key is not set.
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set.")
        
    return value

def get_overpass_api_key() -> Optional[str]:
    """
    Retrieves the Overpass API key.
    
    Returns:
        The API key string or None if not set.
    """
    return get_env_var("OVERPASS_API_KEY")

def get_aws_credentials() -> Dict[str, Optional[str]]:
    """
    Retrieves AWS credentials from environment variables.
    
    Returns:
        A dictionary with 'aws_access_key_id', 'aws_secret_access_key', and 'aws_region'.
    """
    return {
        "aws_access_key_id": get_env_var("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": get_env_var("AWS_SECRET_ACCESS_KEY"),
        "aws_region": get_env_var("AWS_REGION", default="us-east-1")
    }

def validate_required_env_vars(required_keys: List[str]) -> bool:
    """
    Validates that a list of required environment variables are set.
    
    Args:
        required_keys: List of environment variable names that must be present.
        
    Returns:
        True if all keys are present, False otherwise.
        
    Raises:
        ValueError: If any required key is missing.
    """
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info(f"All required environment variables validated: {required_keys}")
    return True

def create_example_env_file() -> Path:
    """
    Creates a .env.example file if it doesn't exist, documenting required keys.
    
    Returns:
        Path to the created .env.example file.
    """
    example_path = get_path("") / ".env.example"
    
    if example_path.exists():
        logger.info(f".env.example already exists at {example_path}")
        return example_path
    
    content = """# Urban Heat Island Analysis - Environment Configuration
# Copy this file to .env and fill in your credentials.
# Do NOT commit .env to version control.

# Overpass API (for OSM data)
# Get a key from https://overpass-api.de/ or use a local instance
OVERPASS_API_KEY=your_overpass_api_key_here

# AWS Credentials (for satellite data if using AWS S3)
# Optional: Only required if fetching data from AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
"""
    
    try:
        with open(example_path, 'w') as f:
            f.write(content)
        logger.info(f"Created .env.example at {example_path}")
    except Exception as e:
        logger.error(f"Failed to create .env.example: {e}")
        raise
    
    return example_path