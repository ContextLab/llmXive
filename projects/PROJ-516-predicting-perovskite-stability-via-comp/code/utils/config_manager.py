"""
Configuration management utilities.
Fixed: Added missing 'List' import from typing.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_dotenv_file(dotenv_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    """
    if dotenv_path is None:
        dotenv_path = Path(__file__).parent.parent.parent / ".env"
    
    if not dotenv_path.exists():
        logger.warning(f".env file not found at {dotenv_path}")
        return False
    
    return load_dotenv(dotenv_path)

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve an API key from environment variables.
    """
    key = os.getenv(f"{service.upper()}_API_KEY")
    if not key:
        logger.warning(f"API key for {service} not found in environment")
    return key

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML config: {e}")

def validate_environment(required_keys: List[str]) -> bool:
    """
    Validate that all required environment variables are set.
    """
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False
    
    return True