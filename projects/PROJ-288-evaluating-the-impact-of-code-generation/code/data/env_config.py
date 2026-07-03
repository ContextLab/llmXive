"""
Environment configuration management for GitHub API tokens and related settings.

This module provides secure loading and validation of environment variables,
specifically focusing on GitHub API tokens required for data acquisition.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

from data.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_environment_variables(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Optional path to the .env file. If None, looks in the project root.
        
    Returns:
        bool: True if .env was found and loaded, False otherwise.
    """
    if env_path is None:
        # Look for .env in the project root (parent of code/)
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    env_path = Path(env_path)
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "Please create one with GITHUB_TOKEN set.")
        return False
    
    try:
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False

def get_github_token(required: bool = True) -> Optional[str]:
    """
    Retrieve the GitHub API token from environment variables.
    
    Args:
        required: If True, raises an error if the token is not found.
                
    Returns:
        Optional[str]: The GitHub token if found, None otherwise.
        
    Raises:
        ValueError: If required=True and token is not found.
    """
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        if required:
            # Check if .env exists but wasn't loaded
            env_path = Path(__file__).parent.parent.parent / ".env"
            if env_path.exists():
                logger.error(
                    "GITHUB_TOKEN not found in environment. "
                    "Did you forget to load the .env file? "
                    "Run: from data.env_config import load_environment_variables; load_environment_variables()"
                )
            raise ValueError(
                "GITHUB_TOKEN environment variable is required but not set. "
                "Please set it in a .env file at the project root or export it."
            )
        else:
            logger.warning("GITHUB_TOKEN not found in environment variables.")
            return None
    
    # Basic validation: GitHub tokens typically start with 'ghp_' or 'gho_'
    if not (token.startswith("ghp_") or token.startswith("gho_") or token.startswith("github_pat_")):
        logger.warning(
            f"GitHub token may be invalid. "
            f"Expected prefix 'ghp_', 'gho_', or 'github_pat_', got: {token[:4] if len(token) >= 4 else token}"
        )
    
    logger.info("GitHub token loaded successfully")
    return token

def validate_github_token(token: str) -> bool:
    """
    Validate the format of a GitHub token.
    
    Args:
        token: The token string to validate.
        
    Returns:
        bool: True if the token format appears valid, False otherwise.
    """
    if not token:
        return False
    
    valid_prefixes = ("ghp_", "gho_", "github_pat_")
    return token.startswith(valid_prefixes)

def setup_github_credentials() -> str:
    """
    Main entry point to set up GitHub credentials.
    
    This function:
    1. Attempts to load the .env file
    2. Retrieves the GITHUB_TOKEN
    3. Validates the token format
    
    Returns:
        str: The validated GitHub token.
        
    Raises:
        ValueError: If token cannot be loaded or is invalid.
    """
    # Try to load .env file
    load_environment_variables()
    
    # Get the token
    token = get_github_token(required=True)
    
    # Validate format
    if not validate_github_token(token):
        raise ValueError(
            f"Invalid GitHub token format. "
            f"Expected prefix 'ghp_', 'gho_', or 'github_pat_'. "
            f"Got: {token[:10]}..."
        )
    
    logger.info("GitHub credentials validated successfully")
    return token

# Convenience function for quick testing
def test_github_connection() -> bool:
    """
    Test if the GitHub token is valid by making a simple API call.
    
    Returns:
        bool: True if the token is valid, False otherwise.
    """
    try:
        import requests
        token = get_github_token(required=False)
        if not token:
            logger.warning("No GitHub token available for testing")
            return False
        
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        
        if response.status_code == 200:
            logger.info("GitHub token is valid")
            return True
        else:
            logger.error(f"GitHub API returned error: {response.status_code}")
            return False
    except ImportError:
        logger.error("requests library not installed. Install with: pip install requests")
        return False
    except Exception as e:
        logger.error(f"Error testing GitHub connection: {e}")
        return False
