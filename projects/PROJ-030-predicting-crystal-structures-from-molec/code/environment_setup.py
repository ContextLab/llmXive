"""
Environment configuration and validation for the Crystal Structure Prediction project.
Handles HuggingFace token and cache path setup.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from logging_config import get_logger, log_event
from config import get_path_absolute

logger = get_logger(__name__)

def load_environment_variables() -> bool:
    """
    Load environment variables from .env file if it exists.
    Returns True if successful, False otherwise.
    """
    project_root = get_path_absolute("")
    env_path = os.path.join(project_root, ".env")
    
    if os.path.exists(env_path):
        loaded = load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}: {loaded}")
        return loaded
    else:
        logger.warning(f"No .env file found at {env_path}. Using system environment variables.")
        return True

def get_hf_token() -> Optional[str]:
    """
    Retrieve the HuggingFace token from environment variables.
    Returns None if not found.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.warning("HF_TOKEN not found in environment variables.")
        return None
    return token

def get_hf_cache_path() -> Optional[str]:
    """
    Retrieve the HuggingFace cache path from environment variables.
    Returns None if not set (will use default).
    """
    cache_path = os.getenv("HF_HOME")
    if cache_path:
        logger.info(f"Using custom HuggingFace cache path: {cache_path}")
        return cache_path
    return None

def validate_hf_environment() -> Dict[str, Any]:
    """
    Validate that the HuggingFace environment is properly configured.
    Returns a dictionary with validation results.
    """
    result = {
        "valid": True,
        "token_present": False,
        "cache_path_configured": False,
        "errors": []
    }

    token = get_hf_token()
    if token:
        result["token_present"] = True
        # Basic validation: check if token is not empty and has reasonable length
        if len(token) < 10:
            result["valid"] = False
            result["errors"].append("HF_TOKEN appears to be invalid (too short)")
    else:
        result["valid"] = False
        result["errors"].append("HF_TOKEN is not set in environment variables")

    cache_path = get_hf_cache_path()
    if cache_path:
        result["cache_path_configured"] = True
        if not os.path.exists(cache_path):
            try:
                os.makedirs(cache_path, exist_ok=True)
                logger.info(f"Created HuggingFace cache directory: {cache_path}")
            except Exception as e:
                result["valid"] = False
                result["errors"].append(f"Failed to create cache directory: {str(e)}")
    else:
        logger.info("Using default HuggingFace cache path")

    return result

def set_hf_environment() -> None:
    """
    Configure the HuggingFace environment for the current process.
    Sets environment variables and logs configuration status.
    """
    # Load .env file if it exists
    load_environment_variables()

    # Get configuration
    token = get_hf_token()
    cache_path = get_hf_cache_path()

    # Set environment variables if not already set
    if token and not os.getenv("HF_TOKEN"):
        os.environ["HF_TOKEN"] = token
    
    if cache_path and not os.getenv("HF_HOME"):
        os.environ["HF_HOME"] = cache_path

    # Validate configuration
    validation = validate_hf_environment()
    
    if validation["valid"]:
        log_event("environment_configured", {
            "token_present": validation["token_present"],
            "cache_path": cache_path or "default"
        })
        logger.info("HuggingFace environment configured successfully")
    else:
        log_event("environment_validation_failed", {
            "errors": validation["errors"]
        })
        logger.error(f"HuggingFace environment validation failed: {validation['errors']}")
        # Don't raise exception here - let downstream components handle missing token

def main() -> int:
    """
    Main entry point for environment configuration script.
    Validates and reports on the current environment configuration.
    """
    logger.info("Starting environment configuration validation...")
    
    # Load environment variables
    load_environment_variables()
    
    # Validate configuration
    validation = validate_hf_environment()
    
    print("\n=== HuggingFace Environment Configuration ===")
    print(f"Token Present: {'Yes' if validation['token_present'] else 'No'}")
    print(f"Cache Path Configured: {'Yes' if validation['cache_path_configured'] else 'No (using default)'}")
    print(f"Overall Valid: {'Yes' if validation['valid'] else 'No'}")
    
    if validation["errors"]:
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    print("\n=== Configuration Complete ===")
    
    return 0 if validation["valid"] else 1

if __name__ == "__main__":
    sys.exit(main())
