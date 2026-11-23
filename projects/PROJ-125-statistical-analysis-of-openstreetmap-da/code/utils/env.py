"""
Environment variable management utilities for the OSM Urban Heat project.
Handles loading .env files, retrieving API keys, and validating required configurations.
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
    # The project root is assumed to be the parent of the 'code' directory
    # or the current working directory if running from root.
    # We look for .env in the current working directory first, then fallback to project root.
    cwd = Path.cwd()
    env_file = cwd / ".env"
    
    if not env_file.exists():
        # Fallback to the directory where config.py lives (project root)
        config_dir = get_path("") # get_path("") returns project root
        env_file = Path(config_dir) / ".env"
        
    return env_file


def load_env_vars(env_path: Optional[Path] = None, override: bool = False) -> bool:
    """
    Loads environment variables from a .env file into os.environ.
    
    Args:
        env_path: Optional explicit path to the .env file. If None, uses get_project_env_path().
        override: If True, overrides existing environment variables with .env values.
                If False, .env values only fill in missing variables.
    
    Returns:
        bool: True if loading was successful (file existed and was processed), False otherwise.
    """
    if env_path is None:
        env_path = get_project_env_path()

    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. Skipping load.")
        return False

    try:
        # dotenv.load_dotenv returns True if the file was found and parsed, False otherwise.
        # override=True forces overwriting existing env vars, which is useful for local dev.
        result = load_dotenv(dotenv_path=env_path, override=override)
        if result:
            logger.info(f"Environment variables loaded from {env_path}")
        else:
            logger.warning(f"Failed to parse environment file at {env_path}")
        return result
    except Exception as e:
        logger.error(f"Error loading environment file {env_path}: {e}")
        return False


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieves an environment variable by key.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raises a ValueError if the variable is missing and no default is provided.
    
    Returns:
        The value of the environment variable, or the default.
    
    Raises:
        ValueError: If required=True and the variable is missing.
    """
    value = os.getenv(key, default)
    
    if value is None and required:
        raise ValueError(f"Required environment variable '{key}' is not set. "
                         f"Please add it to your .env file.")
                         
    return value


def get_overpass_api_key() -> Optional[str]:
    """
    Retrieves the Overpass API key.
    
    Returns:
        The API key string, or None if not set.
    """
    return get_env_var("OVERPASS_API_KEY", required=False)


def get_aws_credentials() -> Dict[str, str]:
    """
    Retrieves AWS credentials for S3 access (if configured).
    
    Returns:
        A dictionary containing 'access_key', 'secret_key', and 'region'.
        Returns empty dict if any are missing.
    """
    access_key = get_env_var("AWS_ACCESS_KEY_ID", required=False)
    secret_key = get_env_var("AWS_SECRET_ACCESS_KEY", required=False)
    region = get_env_var("AWS_DEFAULT_REGION", default="us-east-1", required=False)
    
    if not access_key or not secret_key:
        # Log warning but do not fail; some operations might not need AWS
        logger.warning("AWS credentials not fully configured in .env. "
                       "Some features (e.g., remote data fetching) may fail.")
        return {}
        
    return {
        "access_key": access_key,
        "secret_key": secret_key,
        "region": region
    }


def validate_required_env_vars(required_keys: List[str]) -> bool:
    """
    Validates that a list of required environment variables are set.
    
    Args:
        required_keys: List of environment variable keys that must be present.
    
    Returns:
        bool: True if all are present, False otherwise.
    
    Raises:
        ValueError: If any required key is missing.
    """
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}. "
                         f"Please update your .env file.")
                         
    logger.info(f"All required environment variables validated: {required_keys}")
    return True


def create_example_env_file(output_path: Optional[Path] = None) -> Path:
    """
    Creates an example .env.example file if one does not exist.
    
    Args:
        output_path: Optional path to write the file. Defaults to project root/.env.example.
    
    Returns:
        Path: The path to the created file.
    """
    if output_path is None:
        output_path = get_path(".env.example")
        
    content = """
# Overpass API Configuration
# Get a key from https://overpass-api.de/ or your provider
OVERPASS_API_KEY=your_overpass_api_key_here

# AWS S3 Configuration (Optional - for remote data storage)
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_DEFAULT_REGION=us-east-1

# Other Project Configuration
# MAX_BLOCKS=100
# MISSING_DATA_THRESHOLD=0.1
""".strip()

    if not output_path.exists():
        with open(output_path, 'w') as f:
            f.write(content)
        logger.info(f"Created example environment file at {output_path}")
    else:
        logger.info(f"Example environment file already exists at {output_path}")
        
    return output_path