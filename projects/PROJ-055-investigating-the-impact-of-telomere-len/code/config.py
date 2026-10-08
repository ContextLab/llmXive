"""
Configuration management module for the Telomere-Lifesman Impact project.
Handles environment variable loading, validation, and random seed initialization.
"""
import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

# Project root path (assuming code/ is at repo root or one level up)
# We assume this file is at code/config.py, so root is parent
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE_PATH = PROJECT_ROOT / "code" / ".env"
CONFIG_SCHEMA = {
    "required": ["DRYAD_API_KEY"],
    "optional": ["ANAGE_API_KEY", "RANDOM_SEED"],
    "defaults": {
        "ANAGE_API_KEY": "",
        "RANDOM_SEED": 42
    }
}

def load_env_config(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file into os.environ.
    Supports standard KEY=VALUE format.
    
    Args:
        env_path: Path to the .env file. Defaults to PROJECT_ROOT/code/.env
    
    Returns:
        Dictionary of loaded environment variables.
    
    Raises:
        FileNotFoundError: If the .env file does not exist.
    """
    if env_path is None:
        env_path = ENV_FILE_PATH
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}")
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                env_vars[key] = value
                os.environ[key] = value
    
    return env_vars

def validate_config(config: Dict[str, str]) -> None:
    """
    Validate that required configuration keys are present and non-empty.
    
    Args:
        config: Dictionary of configuration values.
    
    Raises:
        ConfigError: If a required key is missing or empty.
    """
    required_keys = CONFIG_SCHEMA.get("required", [])
    for key in required_keys:
        value = config.get(key)
        if not value:
            raise ConfigError(f"Missing or empty required configuration key: {key}")
    
    # Optional validation: Check if RANDOM_SEED is an integer
    if "RANDOM_SEED" in config:
        try:
            int(config["RANDOM_SEED"])
        except ValueError:
            raise ConfigError(f"RANDOM_SEED must be an integer, got: {config['RANDOM_SEED']}")

def init_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Initialize the project configuration: load .env, validate, and set seeds.
    
    Args:
        env_path: Path to the .env file.
    
    Returns:
        Dictionary containing the validated configuration.
    
    Raises:
        ConfigError: If validation fails.
    """
    try:
        env_vars = load_env_config(env_path)
    except FileNotFoundError:
        # If .env is missing, try to load from actual OS environment
        # This allows CI/CD or production environments to work without a file
        env_vars = {k: v for k, v in os.environ.items() if k in CONFIG_SCHEMA["required"] + CONFIG_SCHEMA["optional"]}
    
    # Apply defaults for optional keys not present
    for key, default_val in CONFIG_SCHEMA.get("defaults", {}).items():
        if key not in env_vars:
            env_vars[key] = str(default_val)
    
    validate_config(env_vars)
    set_random_seed(int(env_vars.get("RANDOM_SEED", 42)))
    
    return env_vars

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration. Initializes it if not already done.
    This is a convenience wrapper for scripts that need config without explicit init.
    
    Returns:
        Configuration dictionary.
    """
    # Simple check if we have the critical key in os.environ
    if "DRYAD_API_KEY" not in os.environ:
        return init_config()
    return {k: v for k, v in os.environ.items() if k in CONFIG_SCHEMA["required"] + CONFIG_SCHEMA["optional"]}

def set_random_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across libraries.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    # If numpy is available, seed it too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # If torch is available, seed it too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    # Log the seed setting
    import logging
    logging.getLogger(__name__).info(f"Random seed set to: {seed}")
