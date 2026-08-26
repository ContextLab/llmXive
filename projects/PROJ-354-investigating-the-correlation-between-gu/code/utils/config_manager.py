import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import keyring

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to project root .env.
        
    Returns:
        bool: True if loaded successfully, False otherwise.
    """
    if env_path is None:
        # Default to project root .env
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "Ensure you have copied code/.env.example to code/.env and filled it.")
        return False
    
    try:
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False

def get_token_from_env(var_name: str) -> Optional[str]:
    """
    Retrieve a token from environment variables.
    
    Args:
        var_name: The name of the environment variable.
        
    Returns:
        The token string if found, None otherwise.
    """
    token = os.getenv(var_name)
    if token:
        logger.debug(f"Found {var_name} in environment variables")
        return token
    logger.debug(f"{var_name} not found in environment variables")
    return None

def get_token_from_keyring(service_name: str, username: str = "ukb_user") -> Optional[str]:
    """
    Retrieve a token from the system keyring.
    
    Args:
        service_name: The name of the service in the keyring.
        username: The username associated with the credential.
        
    Returns:
        The token string if found, None otherwise.
    """
    try:
        token = keyring.get_password(service_name, username)
        if token:
            logger.debug(f"Found token in keyring for service: {service_name}")
            return token
        logger.debug(f"No token found in keyring for service: {service_name}")
        return None
    except Exception as e:
        logger.warning(f"Failed to retrieve token from keyring: {e}")
        return None

def set_token_to_keyring(service_name: str, username: str = "ukb_user", token: str = "") -> bool:
    """
    Store a token in the system keyring.
    
    Args:
        service_name: The name of the service in the keyring.
        username: The username associated with the credential.
        token: The token to store.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        keyring.set_password(service_name, username, token)
        logger.info(f"Token stored securely in keyring for service: {service_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to store token in keyring: {e}")
        return False

def get_uk_biobank_token(service_name: Optional[str] = None) -> Optional[str]:
    """
    Retrieve the UK Biobank access token.
    
    Priority:
    1. Environment variable UKB_ACCESS_TOKEN
    2. System keyring
    
    Args:
        service_name: Optional keyring service name. Defaults to 'llmXive-ukb'.
        
    Returns:
        The token string if found, None otherwise.
    """
    if service_name is None:
        service_name = os.getenv("UKB_KEYRING_SERVICE_NAME", "llmXive-ukb")
    
    # Try environment variable first
    token = get_token_from_env("UKB_ACCESS_TOKEN")
    if token:
        return token
    
    # Try keyring
    token = get_token_from_keyring(service_name)
    return token

def get_uk_biobank_api_key() -> Optional[str]:
    """
    Retrieve the UK Biobank application key.
    
    Priority:
    1. Environment variable UKB_APP_KEY
    
    Returns:
        The API key string if found, None otherwise.
    """
    return get_token_from_env("UKB_APP_KEY")

def validate_credentials() -> Dict[str, Any]:
    """
    Validate that necessary credentials are present.
    
    Returns:
        Dict containing validation status and details.
    """
    result = {
        "valid": False,
        "token_present": False,
        "api_key_present": False,
        "message": ""
    }
    
    token = get_uk_biobank_token()
    api_key = get_uk_biobank_api_key()
    
    result["token_present"] = token is not None
    result["api_key_present"] = api_key is not None
    
    if result["token_present"] and result["api_key_present"]:
        result["valid"] = True
        result["message"] = "All credentials present."
    else:
        missing = []
        if not result["token_present"]:
            missing.append("UKB_ACCESS_TOKEN")
        if not result["api_key_present"]:
            missing.append("UKB_APP_KEY")
        result["message"] = f"Missing credentials: {', '.join(missing)}. " \
                          "Please update your .env file or set environment variables."
    
    return result

def init_config() -> bool:
    """
    Initialize configuration by loading .env and validating credentials.
    
    Returns:
        bool: True if initialization successful, False otherwise.
    """
    # Load .env file
    load_dotenv_file()
    
    # Validate credentials
    validation = validate_credentials()
    
    if validation["valid"]:
        logger.info("Configuration initialized successfully.")
        return True
    else:
        logger.warning(f"Configuration validation failed: {validation['message']}")
        return False

def main():
    """
    Main entry point for testing configuration management.
    """
    print("Initializing UK Biobank configuration...")
    success = init_config()
    
    if success:
        print("✓ Configuration valid.")
        validation = validate_credentials()
        print(f"  - Token present: {validation['token_present']}")
        print(f"  - API Key present: {validation['api_key_present']}")
    else:
        print("✗ Configuration invalid.")
        validation = validate_credentials()
        print(f"  - Message: {validation['message']}")
        print("\nAction required:")
        print("  1. Copy code/.env.example to code/.env")
        print("  2. Fill in your UK Biobank credentials")
        print("  3. Or set environment variables: UKB_ACCESS_TOKEN, UKB_APP_KEY")
        print("  4. Or use keyring to store credentials securely")

if __name__ == "__main__":
    main()