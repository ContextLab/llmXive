"""
Configuration management for llmXive Research Pipeline.
Handles environment variable loading and configuration access.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from . import logger

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Global config dictionary
_config: Dict[str, Any] = {}
_initialized = False

def load_environment() -> bool:
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env was loaded, False otherwise.
    """
    if ENV_FILE_PATH.exists():
        loaded = load_dotenv(ENV_FILE_PATH, override=True)
        logger.info(f"Loaded environment variables from {ENV_FILE_PATH}")
        return loaded
    else:
        logger.warning(f"Environment file not found at {ENV_FILE_PATH}. Using system environment only.")
        return False

def initialize_config() -> Dict[str, Any]:
    """
    Initialize the configuration by loading environment variables and setting defaults.
    
    Returns:
        Dict[str, Any]: The initialized configuration dictionary.
    """
    global _config, _initialized
    
    if _initialized:
        return _config
    
    # Load environment variables
    load_environment()
    
    # Set default configuration values
    _config = {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(PROJECT_ROOT / "data"),
        "code_dir": str(PROJECT_ROOT / "code"),
        "tests_dir": str(PROJECT_ROOT / "tests"),
        "logs_dir": str(PROJECT_ROOT / "logs"),
        "figures_dir": str(PROJECT_ROOT / "figures"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "hf_token": os.getenv("HF_TOKEN", ""),
        "data_source_url": os.getenv("DATA_SOURCE_URL", ""),
    }
    
    _initialized = True
    logger.info("Configuration initialized successfully")
    return _config

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by key.
    
    Args:
        key: The configuration key.
        default: Default value if key is not found.
        
    Returns:
        Any: The configuration value or default.
    """
    if not _initialized:
        initialize_config()
    return _config.get(key, default)

def get_int_config(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Get an integer configuration value.
    
    Args:
        key: The configuration key.
        default: Default value if key is not found or cannot be converted.
        
    Returns:
        Optional[int]: The integer value or default.
    """
    value = get_config_value(key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert config value '{key}'={value} to int")
        return default

def get_float_config(key: str, default: Optional[float] = None) -> Optional[float]:
    """
    Get a float configuration value.
    
    Args:
        key: The configuration key.
        default: Default value if key is not found or cannot be converted.
        
    Returns:
        Optional[float]: The float value or default.
    """
    value = get_config_value(key)
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert config value '{key}'={value} to float")
        return default

def get_bool_config(key: str, default: bool = False) -> bool:
    """
    Get a boolean configuration value.
    
    Args:
        key: The configuration key.
        default: Default value if key is not found.
        
    Returns:
        bool: The boolean value or default.
    """
    value = get_config_value(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)

def get_api_key(service: str) -> Optional[str]:
    """
    Get an API key for a specific service.
    
    Args:
        service: The service name (e.g., 'hf', 'openai').
        
    Returns:
        Optional[str]: The API key or None.
    """
    key_var = f"{service.upper()}_TOKEN"
    return os.getenv(key_var)

def get_data_source_url() -> Optional[str]:
    """
    Get the data source URL from configuration.
    
    Returns:
        Optional[str]: The data source URL or None.
    """
    return get_config_value("data_source_url")

def get_project_config() -> Dict[str, Any]:
    """
    Get the full project configuration.
    
    Returns:
        Dict[str, Any]: The complete configuration dictionary.
    """
    if not _initialized:
        initialize_config()
    return _config.copy()
