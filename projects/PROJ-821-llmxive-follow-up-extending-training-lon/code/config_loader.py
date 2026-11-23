"""
Configuration loader for llmXive project.
Handles environment variable loading with fallback to defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Default configuration values
DEFAULTS = {
    "PROJECT_ROOT": str(Path(__file__).resolve().parent.parent),
    "MODEL_ID": "mmpro/MMProLong-7B-1.0",
    "MAX_TOKENS": "128000",
    "ARM_TYPE": "A",
    "LOG_LEVEL": "INFO",
    "DATA_DIR": "data",
    "MODELS_DIR": "models",
    "RESULTS_DIR": "data/results",
    "ASSETS_DIR": "data/assets",
    "SYNTHETIC_DIR": "data/synthetic",
    "SHORT_CONTEXT_DIR": "data/synthetic/short_context",
}

def load_env():
    """
    Load environment variables from .env file if present, otherwise use defaults.
    
    This function:
    1. Looks for a .env file in the project root
    2. If found, loads variables from it using python-dotenv
    3. If not found, or for any variable not in .env, falls back to DEFAULTS
    4. Sets environment variables for any missing values
    
    Returns:
        None (modifies os.environ in place)
    
    Raises:
        None (silently falls back to defaults if .env is missing)
    """
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    
    # Load .env if it exists, otherwise load_dotenv will just return False
    if env_path.exists():
        load_dotenv(env_path)
    
    # Ensure all default values are set in environment if not already present
    for key, value in DEFAULTS.items():
        if key not in os.environ:
            os.environ[key] = value

def get_config(key: str, default: str = None) -> str:
    """
    Retrieve a configuration value from environment.
    
    Args:
        key: The environment variable name
        default: Fallback value if not in environment (overrides DEFAULTS)
    
    Returns:
        The value as a string
    """
    # First check environment, then defaults, then provided default
    if key in os.environ:
        return os.environ[key]
    if default is not None:
        return default
    return DEFAULTS.get(key, "")

def get_all_config() -> dict:
    """
    Retrieve all configuration values.
    
    Returns:
        Dictionary of all configuration key-value pairs
    """
    return {key: get_config(key) for key in DEFAULTS.keys()}