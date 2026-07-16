import os
from pathlib import Path
from typing import List, Optional
import logging
from dotenv import load_dotenv

# Import project root and token getters from config to ensure consistent path resolution
# Note: We assume config.py is in the same directory or accessible via relative import
try:
    from .config import _PROJECT_ROOT, get_hf_token, get_ncbi_api_key
except ImportError:
    # Fallback for direct execution or different import context
    from code.utils.config import _PROJECT_ROOT, get_hf_token, get_ncbi_api_key

logger = logging.getLogger(__name__)

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Loads the .env file from the project root.
    
    Args:
        env_path: Optional explicit path to .env file. If None, defaults to 
                  {_PROJECT_ROOT}/.env
    
    Returns:
        True if the file was loaded successfully, False otherwise.
    """
    if env_path is None:
        env_path = _PROJECT_ROOT / ".env"
    
    if not env_path.exists():
        logger.warning(f"No .env file found at {env_path}. API keys will be read from OS environment variables.")
        return False
    
    logger.info(f"Loading environment variables from {env_path}")
    success = load_dotenv(dotenv_path=env_path)
    if success:
        logger.info("Environment variables loaded successfully.")
    else:
        logger.warning("Failed to load .env file (file might be empty or malformed).")
    return success

def validate_api_keys(required_keys: Optional[List[str]] = None) -> bool:
    """
    Validates that required API keys are present in the environment.
    
    Args:
        required_keys: List of environment variable names to check. 
                       Defaults to ['HF_TOKEN', 'NCBI_API_KEY'] if None.
    
    Returns:
        True if all required keys are present and non-empty, False otherwise.
    """
    if required_keys is None:
        required_keys = ['HF_TOKEN', 'NCBI_API_KEY']
    
    missing = []
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            missing.append(key)
    
    if missing:
        logger.error(f"Missing required API keys in environment: {missing}. "
                     f"Please set them in .env or export them.")
        return False
    
    logger.info("All required API keys are present.")
    return True

def setup_environment() -> bool:
    """
    Orchestrates the full environment setup:
    1. Loads .env file if it exists.
    2. Validates that critical API keys are available.
    
    Returns:
        True if setup is successful and keys are valid, False otherwise.
    """
    logger.info("Starting environment setup...")
    
    # 1. Load .env
    load_dotenv_file()
    
    # 2. Validate keys
    # We check the specific keys used by the project based on config.py
    is_valid = validate_api_keys(['HF_TOKEN', 'NCBI_API_KEY'])
    
    if not is_valid:
        logger.error("Environment setup failed due to missing API keys.")
        return False
    
    # 3. Optional: Log masked key presence for debugging (never log full values)
    hf_token = get_hf_token()
    ncbi_key = get_ncbi_api_key()
    
    if hf_token:
        logger.debug("HF_TOKEN is configured.")
    if ncbi_key:
        logger.debug("NCBI_API_KEY is configured.")
    
    logger.info("Environment setup completed successfully.")
    return True
