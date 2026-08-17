import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv
from config import get_path

logger = logging.getLogger(__name__)

def get_project_env_path() -> Path:
    """
    Returns the path to the .env file in the project root.
    """
    return get_path(".env")

def load_env_vars(env_path: Optional[Path] = None) -> bool:
    """
    Loads environment variables from the specified .env file.
    If env_path is None, uses the default project .env location.
    
    Returns True if successful, False if the file does not exist.
    Raises ValueError if the file exists but is malformed.
    """
    if env_path is None:
        env_path = get_project_env_path()
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "API keys may be missing. Set them via OS environment variables.")
        return False
    
    try:
        # load_dotenv returns True if the file was found and parsed, False otherwise
        success = load_dotenv(dotenv_path=env_path)
        if success:
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f"Failed to load .env file from {env_path}")
        return success
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
        raise

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieves an environment variable by key.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raises ValueError if the variable is missing.
    
    Returns:
        The value of the environment variable, or the default if provided.
    
    Raises:
        ValueError: If required=True and the variable is not set.
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set. "
                       f"Please add it to your .env file or set it in your OS environment.")
    
    return value

def get_overpass_api_key() -> str:
    """
    Retrieves the Overpass API key from environment variables.
    
    Returns:
        The Overpass API key.
    
    Raises:
        ValueError: If the key is not found.
    """
    return get_env_var("OVERPASS_API_KEY", required=True)

def get_aws_credentials() -> Dict[str, str]:
    """
    Retrieves AWS credentials from environment variables.
    
    Returns:
        A dictionary containing 'aws_access_key_id' and 'aws_secret_access_key'.
    
    Raises:
        ValueError: If required credentials are missing.
    """
    access_key = get_env_var("AWS_ACCESS_KEY_ID", required=True)
    secret_key = get_env_var("AWS_SECRET_ACCESS_KEY", required=True)
    
    return {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key
    }

def validate_required_env_vars(keys: List[str]) -> None:
    """
    Validates that a list of required environment variables are set.
    
    Args:
        keys: List of environment variable names to check.
    
    Raises:
        ValueError: If any of the required variables are missing.
    """
    missing = [key for key in keys if os.getenv(key) is None]
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please ensure they are set in your .env file or OS environment."
        )

def create_example_env_file(output_path: Optional[Path] = None) -> Path:
    """
    Creates an example .env file with placeholders for required keys.
    
    Args:
        output_path: Where to write the example file. Defaults to .env.example in project root.
    
    Returns:
        Path to the created file.
    """
    if output_path is None:
        output_path = get_path(".env.example")
    
    content = """# Overpass API Key
# Get your key from: https://overpass-api.de/api_key
OVERPASS_API_KEY=your_overpass_api_key_here

# AWS Credentials for satellite data (MODIS/Landsat)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# Optional: AWS S3 Bucket for data storage
AWS_S3_BUCKET=your_s3_bucket_name
AWS_DEFAULT_REGION=us-east-1

# Optional: Logging level
LOG_LEVEL=INFO
"""
    
    with open(output_path, "w") as f:
        f.write(content)
    
    logger.info(f"Created example environment file at {output_path}")
    return output_path