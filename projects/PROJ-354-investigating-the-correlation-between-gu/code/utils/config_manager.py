"""
Environment configuration management for credentials.

Handles loading UK Biobank tokens from environment variables or secure keyring,
validating credentials, and initializing the configuration state.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import keyring

from .logging import ConfigError, get_logger

# Logger instance
logger = get_logger(__name__)

# Constants
ENV_FILE_PATH = ".env"
UK_BIOBANK_TOKEN_SERVICE = "llmXive.uk_biobank"
UK_BIOBANK_TOKEN_USER = "api_token"
UK_BIOBANK_API_KEY_SERVICE = "llmXive.uk_biobank_api"
UK_BIOBANK_API_KEY_USER = "api_key"

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file if it exists.

    Args:
        env_path: Path to the .env file. Defaults to project root .env.

    Returns:
        True if file was loaded, False if not found.
    """
    if env_path is None:
        env_path = Path.cwd() / ENV_FILE_PATH

    if not env_path.exists():
        logger.debug(f"No .env file found at {env_path}")
        return False

    logger.info(f"Loading environment variables from {env_path}")
    try:
        load_dotenv(dotenv_path=env_path, override=True)
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        raise ConfigError(f"Failed to load .env file: {e}") from e

def get_token_from_env(var_name: str = "UK_BIOBANK_TOKEN") -> Optional[str]:
    """
    Retrieve a token directly from the environment variable.

    Args:
        var_name: The environment variable name.

    Returns:
        The token string if found, None otherwise.
    """
    token = os.getenv(var_name)
    if token:
        logger.debug(f"Token found in environment variable {var_name}")
        # Mask for logging safety
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
        logger.debug(f"Token loaded (masked): {masked}")
    return token

def get_token_from_keyring(service: str = UK_BIOBANK_TOKEN_SERVICE, user: str = UK_BIOBANK_TOKEN_USER) -> Optional[str]:
    """
    Retrieve a token from the system keyring.

    Args:
        service: The service name for keyring lookup.
        user: The username/key for the credential.

    Returns:
        The token string if found, None otherwise.
    """
    try:
        token = keyring.get_password(service, user)
        if token:
            logger.debug(f"Token found in keyring for {service}/{user}")
        return token
    except Exception as e:
        logger.warning(f"Failed to retrieve token from keyring: {e}")
        return None

def set_token_to_keyring(token: str, service: str = UK_BIOBANK_TOKEN_SERVICE, user: str = UK_BIOBANK_TOKEN_USER) -> None:
    """
    Store a token securely in the system keyring.

    Args:
        token: The token to store.
        service: The service name.
        user: The username/key.
    """
    try:
        keyring.set_password(service, user, token)
        logger.info(f"Token securely stored in keyring for {service}/{user}")
    except Exception as e:
        logger.error(f"Failed to store token in keyring: {e}")
        raise ConfigError(f"Failed to store token in keyring: {e}") from e

def get_uk_biobank_token() -> str:
    """
    Retrieve the UK Biobank token with priority: Env > Keyring > Error.

    Returns:
        The UK Biobank token string.

    Raises:
        ConfigError: If no token is found in environment or keyring.
    """
    # 1. Check Environment Variable
    token = get_token_from_env("UK_BIOBANK_TOKEN")
    if token:
        return token

    # 2. Check Keyring
    token = get_token_from_keyring()
    if token:
        return token

    # 3. Fail loudly
    error_msg = (
        "UK Biobank token not found. "
        "Please set the 'UK_BIOBANK_TOKEN' environment variable "
        "or store it in your system keyring using the setup script."
    )
    logger.error(error_msg)
    raise ConfigError(error_msg)

def get_uk_biobank_api_key() -> str:
    """
    Retrieve the UK Biobank API key (if separate from token) with priority: Env > Keyring > Error.

    Returns:
        The API key string.

    Raises:
        ConfigError: If no key is found.
    """
    key = get_token_from_env("UK_BIOBANK_API_KEY")
    if key:
        return key

    key = get_token_from_keyring(service=UK_BIOBANK_API_KEY_SERVICE, user=UK_BIOBANK_API_KEY_USER)
    if key:
        return key

    error_msg = (
        "UK Biobank API key not found. "
        "Please set the 'UK_BIOBANK_API_KEY' environment variable "
        "or store it in your system keyring."
    )
    logger.error(error_msg)
    raise ConfigError(error_msg)

def validate_credentials() -> Dict[str, bool]:
    """
    Validate that all required credentials are present and accessible.

    Returns:
        A dictionary mapping credential names to their validation status (True/False).
    """
    results = {
        "uk_biobank_token": False,
        "uk_biobank_api_key": False
    }

    try:
        get_uk_biobank_token()
        results["uk_biobank_token"] = True
        logger.info("UK Biobank token validation: PASSED")
    except ConfigError:
        logger.warning("UK Biobank token validation: FAILED")

    try:
        get_uk_biobank_api_key()
        results["uk_biobank_api_key"] = True
        logger.info("UK Biobank API key validation: PASSED")
    except ConfigError:
        logger.warning("UK Biobank API key validation: FAILED")

    return results

def init_config() -> Dict[str, Any]:
    """
    Initialize the configuration by loading .env and validating credentials.

    Returns:
        Configuration dictionary with status and retrieved secrets (masked).

    Raises:
        ConfigError: If critical credentials are missing.
    """
    # Load .env if present
    load_dotenv_file()

    # Validate
    validation = validate_credentials()

    config = {
        "initialized": True,
        "validation": validation,
        "status": "ready" if all(validation.values()) else "missing_credentials"
    }

    if config["status"] == "missing_credentials":
        logger.warning("Configuration initialized but some credentials are missing.")
    else:
        logger.info("Configuration initialized successfully with all credentials present.")

    return config

def main() -> None:
    """
    CLI entry point for credential management and validation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="UK Biobank Credential Manager")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current credentials without modifying state."
    )
    parser.add_argument(
        "--set-token",
        type=str,
        help="Set the UK Biobank token in the keyring (prompts for value if not provided)."
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to .env file (default: ./env)."
    )

    args = parser.parse_args()

    if args.env_file:
        load_dotenv_file(Path(args.env_file))

    if args.set_token:
        token = args.set_token
        if not token:
            import getpass
            token = getpass.getpass("Enter UK Biobank Token: ")
        set_token_to_keyring(token)
        logger.info("Token set successfully.")
    elif args.validate:
        validation = validate_credentials()
        if all(validation.values()):
            print("All credentials valid.")
        else:
            print("Some credentials missing.")
            print(validation)
    else:
        # Default: Just init and report status
        config = init_config()
        print(f"Config Status: {config['status']}")
        print(f"Validation: {config['validation']}")

if __name__ == "__main__":
    main()
