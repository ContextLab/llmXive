"""
Environment configuration management for GitHub API tokens.

This module provides utilities to load, validate, and manage environment
variables required for GitHub API access, specifically the GITHUB_TOKEN.

It ensures that the token is present before any API calls are made,
preventing runtime failures due to missing credentials.
"""
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

# Import the local logging configuration
# Assuming this file is in code/data/ and logging_config is in code/data/
from code.data.logging_config import get_logger

logger = get_logger(__name__)

# Constants
ENV_FILE_NAME = ".env"
ENV_EXAMPLE_NAME = ".env.example"
REQUIRED_VARS = ["GITHUB_TOKEN"]
DEFAULT_RATE_LIMIT_HOURLY = 5000
DEFAULT_BACKOFF_INITIAL = 1
DEFAULT_BACKOFF_MAX = 60
DEFAULT_STRATIFICATION_SEED = 42
DEFAULT_MAX_REVIEW_DAYS = 30


def load_environment_variables(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in the 
                  project root (parent of code/).
                  
    Returns:
        True if loading was successful, False otherwise.
    """
    if env_path is None:
        # Default to looking for .env in the project root
        # Assuming this script is run from the project root or code/
        current_dir = Path(__file__).resolve().parent.parent.parent
        env_path = current_dir / ENV_FILE_NAME
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                       f"Ensure {ENV_EXAMPLE_NAME} is copied to {ENV_FILE_NAME} and filled.")
        return False

    try:
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Successfully loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {e}")
        return False


def get_github_token() -> Optional[str]:
    """
    Retrieve the GitHub API token from the environment.
    
    Returns:
        The token string if found, None otherwise.
    """
    token = os.getenv("GITHUB_TOKEN")
    if token is None:
        logger.error("GITHUB_TOKEN not found in environment. "
                     "Please set it in the .env file.")
    return token


def validate_github_token(token: Optional[str] = None) -> bool:
    """
    Validate that the GitHub token is present and non-empty.
    
    Args:
        token: The token to validate. If None, fetches from environment.
                
    Returns:
        True if the token is valid (non-empty string), False otherwise.
    """
    if token is None:
        token = get_github_token()
    
    if not token or not isinstance(token, str) or len(token.strip()) == 0:
        logger.error("GitHub token is missing or empty.")
        return False
    
    # Basic validation: token should be at least 20 chars (usually 40 for classic)
    if len(token) < 20:
        logger.warning("GitHub token appears unusually short.")
    
    logger.info("GitHub token validation passed.")
    return True


def setup_github_credentials() -> bool:
    """
    Main entry point to setup and validate GitHub credentials.
    
    This function:
    1. Loads the .env file.
    2. Retrieves the token.
    3. Validates the token.
    
    Returns:
        True if setup is successful, False otherwise.
    """
    logger.info("Starting GitHub credentials setup...")
    
    if not load_environment_variables():
        return False
        
    token = get_github_token()
    if not validate_github_token(token):
        return False
        
    logger.info("GitHub credentials setup completed successfully.")
    return True


def get_config() -> dict:
    """
    Retrieve all relevant configuration values from environment variables.
    
    Returns:
        A dictionary containing configuration values.
    """
    load_environment_variables()
    return {
        "github_token": os.getenv("GITHUB_TOKEN"),
        "rate_limit_hourly": int(os.getenv("RATE_LIMIT_HOURLY", DEFAULT_RATE_LIMIT_HOURLY)),
        "backoff_initial": int(os.getenv("BACKOFF_INITIAL", DEFAULT_BACKOFF_INITIAL)),
        "backoff_max": int(os.getenv("BACKOFF_MAX", DEFAULT_BACKOFF_MAX)),
        "stratification_seed": int(os.getenv("STRATIFICATION_SEED", DEFAULT_STRATIFICATION_SEED)),
        "max_review_days": int(os.getenv("MAX_REVIEW_DAYS", DEFAULT_MAX_REVIEW_DAYS)),
    }


def main():
    """
    Command-line interface for testing environment configuration.
    """
    print("Testing Environment Configuration Management...")
    print("-" * 40)
    
    if setup_github_credentials():
        print("✓ GitHub token is configured and valid.")
        config = get_config()
        print(f"  - Rate Limit: {config['rate_limit_hourly']}")
        print(f"  - Backoff Initial: {config['backoff_initial']}s")
        print(f"  - Backoff Max: {config['backoff_max']}s")
        print(f"  - Stratification Seed: {config['stratification_seed']}")
        print(f"  - Max Review Days: {config['max_review_days']}")
    else:
        print("✗ GitHub token configuration failed.")
        print("  Please ensure you have created a .env file based on data/.env.example")
        print("  and added a valid GITHUB_TOKEN.")
        sys.exit(1)

    print("-" * 40)
    print("Environment configuration test complete.")


if __name__ == "__main__":
    main()
