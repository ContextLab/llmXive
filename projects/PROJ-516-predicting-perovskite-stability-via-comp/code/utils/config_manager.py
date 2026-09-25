"""
Configuration management for the project.
Handles loading YAML config and environment variables.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_dotenv_file(path: Optional[Path] = None) -> Dict[str, str]:
    """
    Loads environment variables from a .env file.
    Returns a dictionary of key-value pairs.
    """
    if path is None:
        path = Path(__file__).parent.parent.parent / ".env"
    
    if not path.exists():
        logger.warning(f".env file not found at {path}. Skipping.")
        return {}

    env_vars = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieves an API key for a specific service from environment variables.
    """
    env_vars = load_dotenv_file()
    key_name = f"{service.upper()}_API_KEY"
    return env_vars.get(key_name)

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    """
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    
    if not path.exists():
        raise ConfigError(f"Config file not found at {path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def validate_environment(required_keys: List[str]) -> bool:
    """
    Validates that required environment variables are present.
    """
    env_vars = load_dotenv_file()
    missing = []
    for key in required_keys:
        if key not in env_vars:
            missing.append(key)
    
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False
    
    logger.info("Environment validation passed.")
    return True
