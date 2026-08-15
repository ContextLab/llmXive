"""
Configuration Management Module.
Handles environment variables and project configuration.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from logger import logger

# Load environment variables
load_dotenv()

def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()

def initialize_config():
    """Initialize project configuration."""
    pass

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return os.getenv(key, default)

def get_int_config(key: str, default: int = 0) -> int:
    """Get integer configuration value."""
    val = os.getenv(key)
    return int(val) if val else default

def get_float_config(key: str, default: float = 0.0) -> float:
    """Get float configuration value."""
    val = os.getenv(key)
    return float(val) if val else default

def get_bool_config(key: str, default: bool = False) -> bool:
    """Get boolean configuration value."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes')

def get_api_key(service: str) -> Optional[str]:
    """Get API key for a service."""
    return os.getenv(f"{service.upper()}_API_KEY")

def get_data_source_url() -> str:
    """Get data source URL."""
    return os.getenv("DATA_SOURCE_URL", "")

def get_memory_limit() -> int:
    """Get memory limit in GB."""
    return get_int_config("MEMORY_LIMIT_GB", default=14)

def get_project_config() -> Dict[str, Any]:
    """Get full project configuration."""
    return {
        "memory_limit_gb": get_memory_limit(),
        "data_source_url": get_data_source_url(),
        "api_keys": {
            "materials_project": get_api_key("materials_project"),
            "arxiv": get_api_key("arxiv")
        }
    }
