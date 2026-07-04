"""
Environment variable management.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from config import get_path
from dotenv import load_dotenv

def get_project_env_path() -> Path:
    """
    Get the path to the .env file.
    """
    return get_path("CODE_DIR").parent / ".env"

def load_env_vars() -> bool:
    """
    Load environment variables from .env file.
    
    Returns:
        True if loaded successfully
    """
    env_path = get_project_env_path()
    if env_path.exists():
        load_dotenv(env_path)
        return True
    return False

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.
    """
    return os.getenv(key, default)

def get_overpass_api_key() -> Optional[str]:
    """
    Get the Overpass API key.
    """
    return get_env_var("OVERPASS_API_KEY")

def get_aws_credentials() -> Dict[str, str]:
    """
    Get AWS credentials from environment.
    """
    return {
        "access_key": get_env_var("AWS_ACCESS_KEY_ID"),
        "secret_key": get_env_var("AWS_SECRET_ACCESS_KEY"),
        "region": get_env_var("AWS_REGION", "us-east-1")
    }

def validate_required_env_vars(required: list) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required: List of variable names
        
    Returns:
        True if all are set
    """
    missing = [v for v in required if not get_env_var(v)]
    if missing:
        logging.error(f"Missing required environment variables: {missing}")
        return False
    return True

def create_example_env_file() -> Path:
    """
    Create an example .env file if it doesn't exist.
    """
    env_path = get_project_env_path()
    if not env_path.exists():
        content = """# Overpass API Key
OVERPASS_API_KEY=your_key_here

# AWS Credentials (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
"""
        with open(env_path, 'w') as f:
            f.write(content)
    return env_path