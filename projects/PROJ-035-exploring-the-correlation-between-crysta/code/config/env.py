import os
import logging
from typing import Optional

def load_api_key(key_name: str) -> Optional[str]:
    """
    Loads an API key from an environment variable.

    Args:
        key_name: The name of the environment variable.

    Returns:
        The API key if found, otherwise None.
    """
    api_key = os.getenv(key_name)
    if not api_key:
        logging.error(f"API key not found for: {key_name}")
        return None
    return api_key

def validate_environment() -> bool:
    """
    Validates that required environment variables are set.

    Returns:
        True if all required environment variables are set, False otherwise.
    """
    required_keys = ["MATERIALS_PROJECT_API_KEY"]
    for key in required_keys:
        if not load_api_key(key):
            logging.error(f"Required environment variable not set: {key}")
            return False
    return True

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Sets up a logger.

    Args:
        name: The name of the logger.
        level: The logging level.

    Returns:
        The logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

if __name__ == "__main__":
    # Example usage
    if validate_environment():
        api_key = load_api_key("MATERIALS_PROJECT_API_KEY")
        print(f"API key loaded successfully.")
    else:
        print("Environment validation failed. Please set required environment variables.")