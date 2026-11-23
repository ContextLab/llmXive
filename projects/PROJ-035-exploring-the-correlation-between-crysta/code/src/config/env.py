import os
import sys
import logging
from typing import Optional

LOGGER_NAME = "llmXive.config.env"

def setup_logger(name: str = LOGGER_NAME, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def load_api_key(key_name: str) -> str:
    """
    Load an API key from the environment variable.
    
    Args:
        key_name: The name of the environment variable.
    
    Returns:
        The value of the environment variable.
    
    Raises:
        KeyError: If the environment variable is not set.
    """
    key = os.getenv(key_name)
    if key is None:
        raise KeyError(f"Environment variable '{key_name}' is not set.")
    return key

def validate_environment(required_keys: Optional[list] = None) -> bool:
    """
    Validate that all required environment variables are set.
    
    This function specifically enforces the requirement for MP_API_KEY
    as per FR-001. It exits with code 0 if all required keys are present,
    and code 1 with the error message "MP_API_KEY not set" if missing.
    
    Args:
        required_keys: List of required environment variable names. Defaults to ['MP_API_KEY'].
    
    Returns:
        True if validation passes (only if called without sys.exit logic in a test context,
        but this function is designed to exit on failure per FR-001).
    
    Raises:
        SystemExit: Exits with code 1 if MP_API_KEY is missing.
    """
    if required_keys is None:
        required_keys = ['MP_API_KEY']
    
    logger = setup_logger()
    missing_keys = []
    
    for key in required_keys:
        if key not in os.environ:
            missing_keys.append(key)
    
    if missing_keys:
        # Per FR-001 specific requirement for MP_API_KEY
        if 'MP_API_KEY' in missing_keys:
            logger.error("MP_API_KEY not set")
            sys.exit(1)
        else:
            # Generic handling for other keys if needed in future
            logger.error(f"Missing required environment variables: {missing_keys}")
            sys.exit(1)
    
    logger.info("Environment validation successful. All required API keys present.")
    return True

if __name__ == "__main__":
    # Direct execution for validation check
    validate_environment()
