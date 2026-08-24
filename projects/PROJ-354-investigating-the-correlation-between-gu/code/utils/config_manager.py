"""
Environment configuration management for credentials.

Handles UK Biobank token and other sensitive credentials securely.
Supports loading from environment variables, .env files, or keyring.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import keyring
from keyring.errors import NoKeyringError

from utils.logging import ConfigError, get_logger

logger = get_logger(__name__)

# Service name for keyring storage
KEYRING_SERVICE = "llmXive_uk_biobank"
ENV_TOKEN_VAR = "UK_BIOBANK_TOKEN"
ENV_API_KEY_VAR = "UK_BIOBANK_API_KEY"
DOTENV_PATH = Path(".env")


def load_dotenv_file(dotenv_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        dotenv_path: Path to .env file. Defaults to project root .env.
        
    Returns:
        True if file was loaded successfully, False otherwise.
    """
    if dotenv_path is None:
        dotenv_path = DOTENV_PATH
        
    if not dotenv_path.exists():
        logger.debug(f"No .env file found at {dotenv_path}")
        return False
        
    logger.info(f"Loading environment from {dotenv_path}")
    load_success = load_dotenv(dotenv_path)
    
    if load_success:
        logger.info("Environment variables loaded successfully")
    else:
        logger.warning("Failed to load environment variables from .env")
        
    return load_success


def get_token_from_env(var_name: str) -> Optional[str]:
    """
    Retrieve a token from an environment variable.
    
    Args:
        var_name: Name of the environment variable.
        
    Returns:
        Token value if found, None otherwise.
    """
    token = os.getenv(var_name)
    if token:
        logger.debug(f"Found token in environment variable {var_name}")
        # Mask the token for logging (show only first/last few chars)
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
        logger.debug(f"Token found: {masked}")
    return token


def get_token_from_keyring(service: str = KEYRING_SERVICE) -> Optional[str]:
    """
    Retrieve a token from the system keyring.
    
    Args:
        service: Keyring service name.
        
    Returns:
        Token value if found, None otherwise.
    """
    try:
        token = keyring.get_password(service, "uk_biobank_token")
        if token:
            logger.debug("Found token in system keyring")
        return token
    except NoKeyringError:
        logger.warning("No keyring available on this system")
        return None
    except Exception as e:
        logger.error(f"Error retrieving token from keyring: {e}")
        return None


def set_token_to_keyring(token: str, service: str = KEYRING_SERVICE) -> bool:
    """
    Store a token in the system keyring.
    
    Args:
        token: Token value to store.
        service: Keyring service name.
        
    Returns:
        True if stored successfully, False otherwise.
    """
    try:
        keyring.set_password(service, "uk_biobank_token", token)
        logger.info("Token stored securely in system keyring")
        return True
    except NoKeyringError:
        logger.error("No keyring available to store token")
        return False
    except Exception as e:
        logger.error(f"Error storing token in keyring: {e}")
        return False


def get_uk_biobank_token() -> str:
    """
    Retrieve the UK Biobank token from various sources in priority order:
    1. Environment variable UK_BIOBANK_TOKEN
    2. System keyring
    3. .env file (loaded first)
    
    Raises:
        ConfigError: If no token is found in any source.
        
    Returns:
        The UK Biobank token string.
    """
    # First, try to load from .env if it exists
    load_dotenv_file()
    
    # Priority 1: Environment variable
    token = get_token_from_env(ENV_TOKEN_VAR)
    if token:
        return token
        
    # Priority 2: System keyring
    token = get_token_from_keyring()
    if token:
        return token
        
    # Priority 3: .env file (already loaded, but check again)
    # This is redundant with load_dotenv_file but ensures we catch it
    token = get_token_from_env(ENV_TOKEN_VAR)
    if token:
        return token
        
    # No token found
    error_msg = (
        "UK Biobank token not found. Please set the UK_BIOBANK_TOKEN "
        "environment variable, store it in your system keyring, or "
        "add it to a .env file in the project root."
    )
    logger.error(error_msg)
    raise ConfigError(error_msg)


def get_uk_biobank_api_key() -> Optional[str]:
    """
    Retrieve the UK Biobank API key (if different from token).
    
    Returns:
        API key if found, None otherwise.
    """
    return get_token_from_env(ENV_API_KEY_VAR)


def validate_credentials() -> Dict[str, bool]:
    """
    Validate that all required credentials are available.
    
    Returns:
        Dictionary with credential names as keys and validation status as values.
    """
    results = {}
    
    # Check UK Biobank token
    try:
        get_uk_biobank_token()
        results["uk_biobank_token"] = True
        logger.info("UK Biobank token: VALID")
    except ConfigError:
        results["uk_biobank_token"] = False
        logger.warning("UK Biobank token: MISSING")
        
    # Check API key (optional)
    api_key = get_uk_biobank_api_key()
    results["uk_biobank_api_key"] = api_key is not None
    if api_key:
        logger.info("UK Biobank API key: VALID")
    else:
        logger.debug("UK Biobank API key: NOT SET (optional)")
        
    return results


def init_config() -> None:
    """
    Initialize configuration management.
    
    This function should be called at the start of the application
    to ensure environment variables are loaded and credentials are validated.
    """
    logger.info("Initializing configuration management")
    
    # Load .env file
    load_dotenv_file()
    
    # Validate credentials
    validation_results = validate_credentials()
    
    # Log summary
    all_valid = all(validation_results.values())
    if all_valid:
        logger.info("All required credentials are valid")
    else:
        missing = [k for k, v in validation_results.items() if not v]
        logger.warning(f"Missing credentials: {', '.join(missing)}")
        
    return validation_results


def main() -> None:
    """
    Command-line interface for configuration management.
    
    Usage:
        python -m utils.config_manager --validate
        python -m utils.config_manager --store-token
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="UK Biobank Configuration Management")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate that all required credentials are available"
    )
    parser.add_argument(
        "--store-token",
        action="store_true",
        help="Store UK Biobank token in system keyring (interactive)"
    )
    parser.add_argument(
        "--show-status",
        action="store_true",
        help="Show current credential status"
    )
    
    args = parser.parse_args()
    
    # Initialize logging
    init_logging()
    
    if args.validate or args.show_status:
        results = validate_credentials()
        print("\nCredential Status:")
        print("-" * 30)
        for name, valid in results.items():
            status = "✓ VALID" if valid else "✗ MISSING"
            print(f"{name}: {status}")
            
    if args.store_token:
        print("Enter your UK Biobank token (will not be echoed):")
        import getpass
        token = getpass.getpass()
        
        if store_token_to_keyring(token):
            print("Token stored successfully!")
        else:
            print("Failed to store token.")


if __name__ == "__main__":
    main()
