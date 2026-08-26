"""
Credentials management module for UK Biobank access.

This module provides secure handling of access tokens using:
1. Environment variables (.env file)
2. OS keyring (for persistent storage)

It fails loudly if credentials are missing, preventing silent fallbacks.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import keyring

from utils.logging import get_logger, ConfigError

logger = get_logger(__name__)

# Constants
ENV_FILE_NAME = ".env"
KEYRING_SERVICE_NAME = "uk_biobank_credentials"
KEYRING_USERNAME = "ukb_access_token"
ENV_TOKEN_VAR = "UKB_ACCESS_TOKEN"

def load_dotenv_file(project_root: Optional[Path] = None) -> bool:
    """
    Load the .env file from the project root.
    
    Args:
        project_root: Path to the project root. Defaults to the directory
                      containing this module's parent.
                      
    Returns:
        True if the file was loaded successfully, False otherwise.
    """
    if project_root is None:
        # Default to the directory two levels up from this file
        project_root = Path(__file__).resolve().parent.parent.parent
        
    env_path = project_root / ENV_FILE_NAME
    
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                     "Please create a .env file with your credentials.")
        return False
        
    logger.info(f"Loading environment variables from {env_path}")
    success = load_dotenv(env_path)
    return success

def get_token_from_env() -> Optional[str]:
    """
    Retrieve the UK Biobank token from environment variables.
    
    Returns:
        The token string if found, None otherwise.
    """
    token = os.getenv(ENV_TOKEN_VAR)
    if token:
        logger.info("UK Biobank token loaded from environment variable.")
    return token

def get_token_from_keyring() -> Optional[str]:
    """
    Retrieve the UK Biobank token from the system keyring.
    
    Returns:
        The token string if found, None otherwise.
    """
    try:
        token = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME)
        if token:
            logger.info("UK Biobank token loaded from system keyring.")
        return token
    except Exception as e:
        logger.warning(f"Failed to retrieve token from keyring: {e}")
        return None

def set_token_to_keyring(token: str) -> bool:
    """
    Store the UK Biobank token in the system keyring.
    
    Args:
        token: The token string to store.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME, token)
        logger.info("UK Biobank token stored in system keyring.")
        return True
    except Exception as e:
        logger.error(f"Failed to store token in keyring: {e}")
        return False

def get_uk_biobank_token() -> str:
    """
    Retrieve the UK Biobank access token.
    
    This function attempts to load the token from the following sources
    in order of precedence:
    1. Environment variables (.env file loaded first)
    2. System keyring
    
    Raises:
        ConfigError: If no token is found in any source.
        
    Returns:
        The UK Biobank access token string.
    """
    # Ensure .env is loaded
    load_dotenv_file()
    
    # Try environment variable first
    token = get_token_from_env()
    if token:
        return token
        
    # Try keyring
    token = get_token_from_keyring()
    if token:
        return token
        
    # Fallback: Raise error
    raise ConfigError(
        "UK Biobank access token not found. "
        "Please set 'UKB_ACCESS_TOKEN' in a .env file or store it in your system keyring. "
        "See code/.env.example for instructions."
    )

def get_uk_biobank_api_key() -> Optional[str]:
    """
    Retrieve the optional UK Biobank API key.
    
    Returns:
        The API key string if found, None otherwise.
    """
    return os.getenv("UKB_API_KEY")

def validate_credentials() -> bool:
    """
    Validate that required credentials are present.
    
    Returns:
        True if credentials are valid, False otherwise.
        
    Raises:
        ConfigError: If credentials are missing.
    """
    try:
        token = get_uk_biobank_token()
        if not token or len(token.strip()) == 0:
            raise ConfigError("UK Biobank token is empty or invalid.")
        logger.info("UK Biobank credentials validation passed.")
        return True
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Error validating credentials: {e}")

def init_config() -> None:
    """
    Initialize the configuration by validating credentials.
    
    This function should be called at the start of any script
    that requires UK Biobank access.
    """
    validate_credentials()
    logger.info("Configuration initialized successfully.")

def main() -> None:
    """
    Command-line interface for credential management.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="UK Biobank Credential Manager")
    parser.add_argument(
        "--store",
        action="store_true",
        help="Store a new token in the keyring (interactive)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current credentials"
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Load from .env file and print status"
    )
    
    args = parser.parse_args()
    
    if args.store:
        token = input("Enter UK Biobank Access Token: ")
        if set_token_to_keyring(token):
            print("Token stored successfully.")
        else:
            print("Failed to store token.")
            
    elif args.validate:
        try:
            if validate_credentials():
                print("Credentials are valid.")
            else:
                print("Credentials validation failed.")
        except ConfigError as e:
            print(f"Validation error: {e}")
            
    elif args.env:
        load_dotenv_file()
        if get_token_from_env():
            print("Token found in .env file.")
        else:
            print("No token found in .env file.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
