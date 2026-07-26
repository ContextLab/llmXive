"""
Environment configuration management for llmXive pipeline.
Handles .env file loading and Hugging Face token retrieval.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_environment(env_path: Path = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in project root.
    
    Returns:
        bool: True if loaded successfully, False otherwise.
    """
    if env_path is None:
        # Default to project root .env
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using system environment only.")
        return False
    
    try:
        success = load_dotenv(dotenv_path=env_path, override=True)
        if success:
            logger.info(f"Environment loaded from {env_path}")
        else:
            logger.warning(f"No variables loaded from {env_path}")
        return success
    except Exception as e:
        logger.error(f"Failed to load environment from {env_path}: {e}")
        return False

def get_hf_token(required: bool = True) -> str:
    """
    Retrieve the Hugging Face API token from environment.
    
    Args:
        required: If True, raise an error if token is missing.
    
    Returns:
        str: The HF token.
    
    Raises:
        RuntimeError: If token is missing and required=True.
    """
    token = os.getenv("HF_TOKEN")
    
    if not token:
        if required:
            error_msg = (
                "Hugging Face token (HF_TOKEN) not found in environment. "
                "Please set it in the .env file or as an environment variable. "
                "Get a token from: https://huggingface.co/settings/tokens"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return None
    
    # Mask token in logs for security
    masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
    logger.info(f"HF Token loaded: {masked_token}")
    return token

def get_env_var(var_name: str, default: str = None, required: bool = False) -> str:
    """
    Retrieve a generic environment variable.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not set.
        required: If True, raise error if missing.
    
    Returns:
        str: The variable value.
    
    Raises:
        RuntimeError: If required and missing.
    """
    value = os.getenv(var_name, default)
    
    if value is None and required:
        error_msg = f"Required environment variable '{var_name}' is not set."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    return value

def main():
    """
    Main entry point for testing environment configuration.
    """
    logger.info("Testing environment configuration...")
    
    # Load environment
    load_environment()
    
    # Test HF token retrieval
    try:
        token = get_hf_token(required=False)
        if token:
            logger.info("SUCCESS: HF token found")
        else:
            logger.warning("WARNING: HF token not found (expected if .env not set)")
    except RuntimeError as e:
        logger.error(f"ERROR: {e}")
    
    # Test generic variable
    test_var = get_env_var("TEST_VAR", default="default_value")
    logger.info(f"TEST_VAR value: {test_var}")

if __name__ == "__main__":
    main()