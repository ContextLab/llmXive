"""
Environment setup utility to load .env file and validate API keys.

This script ensures that the required environment variables for
Materials Project and OpenKIM API keys are set before running the pipeline.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment(env_path: str = ".env") -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file relative to project root.
        
    Returns:
        True if environment loaded successfully, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / env_path
    
    if not env_file.exists():
        logger.warning(f"Environment file not found at {env_file}. "
                     "Please create a .env file with required API keys.")
        return False
    
    load_result = load_dotenv(env_file)
    if load_result:
        logger.info(f"Successfully loaded environment from {env_file}")
        return True
    else:
        logger.error(f"Failed to load environment from {env_file}")
        return False

def validate_api_keys() -> tuple[bool, list[str]]:
    """
    Validate that required API keys are set in the environment.
    
    Returns:
        Tuple of (is_valid, list_of_missing_keys)
    """
    required_keys = [
        "MP_API_KEY",
        "OPENKIM_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    is_valid = len(missing_keys) == 0
    
    if not is_valid:
        logger.error(f"Missing required API keys: {missing_keys}")
        logger.error("Please ensure these keys are set in your .env file or environment.")
    else:
        logger.info("All required API keys are present.")
    
    return is_valid, missing_keys

def main():
    """Main entry point for environment setup validation."""
    logger.info("Starting environment setup validation...")
    
    # Load .env file
    if not load_environment():
        logger.error("Failed to load environment. Exiting.")
        sys.exit(1)
    
    # Validate API keys
    is_valid, missing_keys = validate_api_keys()
    
    if not is_valid:
        logger.error("API key validation failed. Please set the missing keys.")
        sys.exit(1)
    
    logger.info("Environment setup validation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())