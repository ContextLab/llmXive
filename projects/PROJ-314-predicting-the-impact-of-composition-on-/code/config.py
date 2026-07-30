import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from . import logger

# Load environment variables from .env file
# This resolves T011 requirement for environment configuration management
def load_environment():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
    else:
        logger.warning(".env file not found. Using system environment variables.")

# Initialize config by loading environment
load_environment()

def initialize_config():
    """Initialize global configuration state."""
    # This function can be extended to load more complex configs if needed
    pass

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a configuration value from environment variables."""
    return os.getenv(key, default)

def get_int_config(key: str, default: Optional[int] = None) -> Optional[int]:
    """Get an integer configuration value."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        logger.error(f"Invalid integer for config key {key}: {val}")
        return default

def get_float_config(key: str, default: Optional[float] = None) -> Optional[float]:
    """Get a float configuration value."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        logger.error(f"Invalid float for config key {key}: {val}")
        return default

def get_bool_config(key: str, default: Optional[bool] = None) -> Optional[bool]:
    """Get a boolean configuration value."""
    val = os.getenv(key)
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if val.lower() in ('true', '1', 'yes', 'on'):
        return True
    if val.lower() in ('false', '0', 'no', 'off'):
        return False
    logger.warning(f"Invalid boolean for config key {key}: {val}")
    return default

def get_api_key(service: str = "MATERIALS_PROJECT") -> Optional[str]:
    """Get API key for a specific service."""
    key_name = f"{service}_API_KEY"
    return os.getenv(key_name)

def get_data_source_url() -> Optional[str]:
    """Get the data source URL from environment."""
    return os.getenv("DATA_SOURCE_URL")

def get_project_config() -> Dict[str, Any]:
    """Get a dictionary of all relevant project configurations."""
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_file": os.getenv("LOG_FILE", "logs/pipeline.log"),
        "data_source_url": get_data_source_url(),
        "materials_project_key": get_api_key("MATERIALS_PROJECT"),
    }
