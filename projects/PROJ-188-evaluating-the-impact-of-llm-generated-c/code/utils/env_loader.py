"""
Environment variable loading utilities for HuggingFace token and model paths.

This module provides functions to safely load, validate, and retrieve
environment variables required for the llmXive pipeline, specifically:
- HF_TOKEN: HuggingFace API token for model access
- HF_HOME: Custom path for HuggingFace cache
- MODEL_PATH: Override path for specific model binaries
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_VARS = ['HF_TOKEN']
OPTIONAL_VARS = ['HF_HOME', 'MODEL_PATH']

def load_env_vars(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file or system environment.
    
    Args:
        env_path: Optional path to .env file. If None, looks for .env in
                 current directory and parent directories.
    
    Returns:
        Dictionary of loaded environment variables.
    
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Load from .env file if it exists
    if env_path:
        if not Path(env_path).exists():
            logger.warning(f"Specified .env file not found: {env_path}")
        else:
            load_dotenv(env_path)
            logger.info(f"Loaded environment from: {env_path}")
    else:
        # Try to find .env in standard locations
        for potential_path in [".env", "../.env", "../../.env"]:
            if Path(potential_path).exists():
                load_dotenv(potential_path)
                logger.info(f"Loaded environment from: {potential_path}")
                break
        else:
            logger.info("No .env file found, using system environment variables")

    # Validate required variables
    missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Collect all loaded variables
    loaded_vars = {}
    for var in REQUIRED_VARS + OPTIONAL_VARS:
        value = os.getenv(var)
        if value:
            loaded_vars[var] = value
            logger.info(f"Loaded {var}: {'*' * 8}")  # Mask sensitive values

    return loaded_vars

def get_model_path(model_name: Optional[str] = None) -> Path:
    """
    Get the path for model storage or specific model override.
    
    Priority:
    1. MODEL_PATH environment variable (if set)
    2. HF_HOME environment variable (if set)
    3. Default: ~/.cache/huggingface/hub
    
    Args:
        model_name: Optional specific model name to append to path.
    
    Returns:
        Path object pointing to model directory.
    """
    # Check for explicit model path override
    if os.getenv('MODEL_PATH'):
        base_path = Path(os.getenv('MODEL_PATH'))
        logger.info(f"Using explicit MODEL_PATH: {base_path}")
    elif os.getenv('HF_HOME'):
        base_path = Path(os.getenv('HF_HOME')) / 'hub'
        logger.info(f"Using HF_HOME: {base_path}")
    else:
        base_path = Path.home() / '.cache' / 'huggingface' / 'hub'
        logger.info(f"Using default HF cache: {base_path}")

    # Ensure directory exists
    base_path.mkdir(parents=True, exist_ok=True)

    if model_name:
        return base_path / model_name
    return base_path

def validate_token(token: Optional[str] = None) -> bool:
    """
    Validate the HuggingFace token format and presence.
    
    Args:
        token: Optional token string. If None, reads from HF_TOKEN env var.
    
    Returns:
        True if token is valid, False otherwise.
    
    Raises:
        ValueError: If token is missing or invalid format.
    """
    if token is None:
        token = os.getenv('HF_TOKEN')

    if not token:
        logger.error("HuggingFace token is missing")
        return False

    # Basic format validation: should start with 'hf_' and be reasonably long
    if not token.startswith('hf_') or len(token) < 10:
        logger.error(f"Invalid HuggingFace token format: {token[:5]}...")
        return False

    logger.info("HuggingFace token validation passed")
    return True

def main():
    """
    Main entry point for testing environment loading.
    
    This function demonstrates the usage of the env_loader module
    and validates that all required environment variables are properly set.
    """
    try:
        # Load environment variables
        env_vars = load_env_vars()
        
        # Validate token
        if not validate_token():
            logger.error("Token validation failed. Exiting.")
            return 1
        
        # Get model path
        model_path = get_model_path()
        logger.info(f"Model path configured: {model_path}")
        
        logger.info("Environment configuration successful!")
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
