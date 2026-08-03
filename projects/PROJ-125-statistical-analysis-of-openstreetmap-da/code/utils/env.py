"""
Environment variable management utilities for the UHI OSM pipeline.
Handles loading .env files, retrieving specific API keys, and validation.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from dotenv import load_dotenv
from config import get_path

# Configure logger
logger = logging.getLogger(__name__)

def get_project_env_path() -> Path:
    """
    Returns the path to the .env file in the project root.
    """
    # Assuming the project root is the parent of the 'code' directory
    code_dir = get_path("code")
    return code_dir.parent / ".env"

def load_env_vars(env_path: Optional[Path] = None, override: bool = False) -> bool:
    """
    Loads environment variables from the .env file.
    
    Args:
        env_path: Path to the .env file. If None, uses the default project path.
        override: If True, overwrites existing environment variables.
    
    Returns:
        True if loaded successfully, False otherwise.
    """
    if env_path is None:
        env_path = get_project_env_path()
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using system environment only.")
        return False
    
    try:
        # load_dotenv returns True if the file was found and processed
        result = load_dotenv(dotenv_path=env_path, override=override)
        if result:
            logger.info(f"Loaded environment variables from {env_path}")
        return result
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieves an environment variable by key.
    
    Args:
        key: The environment variable key.
        default: Default value if the key is not found.
        required: If True, raises an error if the key is missing.
    
    Returns:
        The value of the environment variable, or the default.
    
    Raises:
        ValueError: If required=True and the key is missing.
    """
    value = os.getenv(key, default)
    
    if required and (value is None or value == ""):
        raise ValueError(f"Required environment variable '{key}' is not set.")
    
    return value

def get_overpass_api_key() -> Optional[str]:
    """
    Retrieves the Overpass API key.
    """
    return get_env_var("OVERPASS_API_KEY")

def get_aws_credentials() -> Dict[str, Optional[str]]:
    """
    Retrieves AWS credentials from environment variables.
    
    Returns:
        A dictionary containing AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION.
    """
    return {
        "access_key": get_env_var("AWS_ACCESS_KEY_ID"),
        "secret_key": get_env_var("AWS_SECRET_ACCESS_KEY"),
        "region": get_env_var("AWS_DEFAULT_REGION", "us-east-1")
    }

def validate_required_env_vars(required_keys: List[str]) -> bool:
    """
    Validates that a list of required environment variables are set.
    
    Args:
        required_keys: List of keys that must be present.
    
    Returns:
        True if all required keys are present, False otherwise.
    """
    missing = []
    for key in required_keys:
        if not get_env_var(key):
            missing.append(key)
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    logger.info("All required environment variables are present.")
    return True

def create_example_env_file() -> Path:
    """
    Creates a .env.example file with placeholder values if it doesn't exist.
    
    Returns:
        Path to the created example file.
    """
    example_path = get_project_env_path().parent / ".env.example"
    
    if example_path.exists():
        logger.info(f"Example env file already exists at {example_path}")
        return example_path
    
    content = """# OpenStreetMap Overpass API Key (if required by your provider)
# Leave empty if using the public free tier without authentication
OVERPASS_API_KEY=

# AWS Credentials for S3/EC2 access (if using AWS-hosted datasets)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

# Optional: Logging level override
LOG_LEVEL=INFO
"""
    try:
        with open(example_path, 'w') as f:
            f.write(content)
        logger.info(f"Created example env file at {example_path}")
    except Exception as e:
        logger.error(f"Failed to create example env file: {e}")
    
    return example_path