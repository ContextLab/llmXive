"""
Configuration Loader Module.
Handles loading of simulation_config.yaml and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Define project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

CONFIG_PATH = PROJECT_ROOT / "config" / "simulation_config.yaml"
ENV_PATH = PROJECT_ROOT / "config" / ".env"

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env() -> bool:
    """
    Load environment variables from .env file if it exists.
    Returns True if loaded, False otherwise.
    """
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        return True
    return False

def load_config() -> Dict[str, Any]:
    """
    Load the main simulation configuration from YAML.
    
    Returns:
        Dict containing the configuration.
        
    Raises:
        ConfigError: If the config file is missing or invalid.
    """
    if not CONFIG_PATH.exists():
        raise ConfigError(f"Configuration file not found at {CONFIG_PATH}")

    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ConfigError("Configuration file must contain a YAML dictionary.")
        
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading configuration file: {e}")

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific value from the config, supporting dot notation.
    
    Example: get_config_value("synthetic_data.corpus_size")
    
    Args:
        key: Dot-separated key path (e.g., "execution_limits.MAX_RUNTIME_SECONDS")
        default: Default value if key is not found
        
    Returns:
        The value or default.
    """
    config = load_config()
    keys = key.split(".")
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value

# Initialize environment on module import
load_env()
