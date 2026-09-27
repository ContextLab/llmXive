"""
Environment configuration management for HuggingFace integration.
Handles token retrieval, cache path configuration, and validation.
"""
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from logging_config import get_logger, log_event
from config import get_path_absolute

logger = get_logger(__name__)

def load_environment_variables() -> bool:
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env was loaded, False otherwise.
    """
    project_root = get_path_absolute(".")
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        log_event(logger, "info", "Environment variables loaded from .env file", path=str(env_path))
        return True
    else:
        log_event(logger, "warning", ".env file not found. Using system environment variables.")
        return False

def get_hf_token() -> Optional[str]:
    """
    Retrieve the HuggingFace token from environment variables.
    
    Checks:
        1. HF_TOKEN environment variable
        2. .env file (if loaded)
        
    Returns:
        Optional[str]: The token if found, None otherwise.
    """
    token = os.getenv("HF_TOKEN")
    
    if not token:
        # Try to load from .env if not already loaded
        load_environment_variables()
        token = os.getenv("HF_TOKEN")
    
    if token:
        log_event(logger, "debug", "HuggingFace token found in environment")
        return token
    else:
        log_event(logger, "warning", "HuggingFace token not found in environment variables")
        return None

def get_hf_cache_path() -> Path:
    """
    Retrieve the HuggingFace cache directory path.
    
    Checks:
        1. HF_HOME environment variable
        2. Default to ~/.cache/huggingface
        
    Returns:
        Path: The cache directory path.
    """
    cache_path = os.getenv("HF_HOME")
    
    if cache_path:
        log_event(logger, "debug", f"Using custom HF_HOME: {cache_path}")
        return Path(cache_path)
    else:
        default_path = Path.home() / ".cache" / "huggingface"
        log_event(logger, "debug", f"Using default HF cache: {default_path}")
        return default_path

def validate_hf_environment() -> bool:
    """
    Validate that the HuggingFace environment is properly configured.
    
    Checks:
        1. HF_TOKEN is set
        2. HF_HOME directory exists or can be created
        
    Returns:
        bool: True if environment is valid, False otherwise.
    """
    token = get_hf_token()
    cache_path = get_hf_cache_path()
    
    if not token:
        log_event(logger, "error", "HuggingFace token is not set. Please set HF_TOKEN environment variable.")
        return False
    
    # Ensure cache directory exists
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        log_event(logger, "info", f"HuggingFace cache directory ready: {cache_path}")
    except Exception as e:
        log_event(logger, "error", f"Failed to create HuggingFace cache directory: {e}")
        return False
    
    return True

def set_hf_environment() -> bool:
    """
    Configure the HuggingFace environment for the current process.
    
    Actions:
        1. Load environment variables from .env
        2. Set HF_HOME environment variable
        3. Validate the configuration
        
    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    load_environment_variables()
    
    # Set HF_HOME for the current process
    cache_path = get_hf_cache_path()
    os.environ["HF_HOME"] = str(cache_path)
    
    # Ensure the directory exists
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log_event(logger, "error", f"Failed to create cache directory: {e}")
        return False
    
    # Validate configuration
    if not validate_hf_environment():
        return False
    
    log_event(logger, "info", "HuggingFace environment configured successfully")
    return True

def main():
    """
    Main function to demonstrate environment configuration.
    """
    print("Configuring HuggingFace environment...")
    
    if set_hf_environment():
        print("✓ Environment configured successfully")
        print(f"  Token: {'*' * 8} (found)" if get_hf_token() else "  Token: NOT FOUND")
        print(f"  Cache: {get_hf_cache_path()}")
        return 0
    else:
        print("✗ Failed to configure environment")
        print("  Please ensure HF_TOKEN is set in your .env file or environment variables.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
