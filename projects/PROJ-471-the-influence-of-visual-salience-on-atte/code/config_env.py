import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def setup_environment(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to the .env file. Defaults to project root .env.
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using system environment variables.")
        return

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Strip quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        logger.info(f"Environment variables loaded from {env_path}")
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        raise

def get_env_value(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get a string value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
        required: If True, raise ValueError if key is missing.
        
    Returns:
        The environment variable value or default.
        
    Raises:
        ValueError: If required is True and key is not found.
    """
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

def get_env_int(key: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
    """
    Get an integer value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
        required: If True, raise ValueError if key is missing.
        
    Returns:
        The environment variable value as int or default.
        
    Raises:
        ValueError: If the value cannot be converted to int or if required and missing.
    """
    value = get_env_value(key, default, required)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' must be an integer, got '{value}'")

def get_env_float(key: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
    """
    Get a float value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
        required: If True, raise ValueError if key is missing.
        
    Returns:
        The environment variable value as float or default.
        
    Raises:
        ValueError: If the value cannot be converted to float or if required and missing.
    """
    value = get_env_value(key, default, required)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable '{key}' must be a float, got '{value}'")

def get_env_bool(key: str, default: Optional[bool] = None, required: bool = False) -> Optional[bool]:
    """
    Get a boolean value from environment variables.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not found.
        required: If True, raise ValueError if key is missing.
        
    Returns:
        The environment variable value as bool or default.
        
    Raises:
        ValueError: If the value cannot be converted to bool or if required and missing.
    """
    value = get_env_value(key, default, required)
    if value is None:
        return None
    if value.lower() in ('true', '1', 'yes', 'on'):
        return True
    elif value.lower() in ('false', '0', 'no', 'off'):
        return False
    else:
        raise ValueError(f"Environment variable '{key}' must be a boolean, got '{value}'")

def validate_required_env_vars(required_vars: list) -> Dict[str, Any]:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names.
        
    Returns:
        Dictionary with 'valid' (bool) and 'missing' (list of missing vars).
        
    Raises:
        ValueError: If any required variables are missing.
    """
    missing = []
    for var in required_vars:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All required environment variables are set")
    return {"valid": True, "missing": []}

def create_env_template(output_path: Optional[Path] = None) -> None:
    """
    Create a .env.example template file with common project variables.
    
    Args:
        output_path: Path to write the template. Defaults to project root .env.example.
    """
    if output_path is None:
        output_path = Path.cwd() / ".env.example"
    
    template_content = """# Project Configuration
# Copy this file to .env and fill in your values

# Paths
DATA_DIR=data
CODE_DIR=code
FIGURES_DIR=figures

# Seeds
RANDOM_SEED=42

# Hyperparameters
BATCH_SIZE=32
LEARNING_RATE=0.001

# Resource Limits
MAX_MEMORY_GB=7
MAX_CPU_TIME_HOURS=6

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/experiment.log

# Dataset
DATASET_NAME=visual_salience_study
DATASET_VERSION=1.0.0

# Model
MODEL_NAME=deepgaze2
DEVICE_TYPE=cpu
"""
    try:
        with open(output_path, 'w') as f:
            f.write(template_content)
        logger.info(f"Created environment template at {output_path}")
    except Exception as e:
        logger.error(f"Failed to create .env template: {e}")
        raise

def init_config() -> None:
    """
    Initialize the configuration environment.
    
    This function:
    1. Sets up environment variables from .env file
    2. Creates .env.example template if it doesn't exist
    3. Validates required environment variables
    """
    # Setup environment from .env
    setup_environment()
    
    # Create template if missing
    template_path = Path.cwd() / ".env.example"
    if not template_path.exists():
        create_env_template(template_path)
    
    # Validate required variables (example list - customize as needed)
    # In a real implementation, you might want to make this configurable
    required_vars = [
        "DATA_DIR",
        "CODE_DIR",
        "RANDOM_SEED"
    ]
    
    try:
        validate_required_env_vars(required_vars)
    except ValueError as e:
        logger.warning(f"Configuration validation failed: {e}")
        logger.warning("Continuing with available environment variables")

def get_env_config() -> Dict[str, Any]:
    """
    Get a dictionary of all environment variables relevant to the project.
    
    Returns:
        Dictionary of environment variables.
    """
    config = {
        "paths": {
            "data_dir": os.environ.get("DATA_DIR", "data"),
            "code_dir": os.environ.get("CODE_DIR", "code"),
            "figures_dir": os.environ.get("FIGURES_DIR", "figures"),
            "log_file": os.environ.get("LOG_FILE", "logs/experiment.log")
        },
        "seeds": {
            "random_seed": int(os.environ.get("RANDOM_SEED", 42))
        },
        "hyperparams": {
            "batch_size": int(os.environ.get("BATCH_SIZE", 32)),
            "learning_rate": float(os.environ.get("LEARNING_RATE", 0.001))
        },
        "limits": {
            "max_memory_gb": int(os.environ.get("MAX_MEMORY_GB", 7)),
            "max_cpu_time_hours": int(os.environ.get("MAX_CPU_TIME_HOURS", 6))
        },
        "logging": {
            "log_level": os.environ.get("LOG_LEVEL", "INFO")
        },
        "dataset": {
            "name": os.environ.get("DATASET_NAME", "visual_salience_study"),
            "version": os.environ.get("DATASET_VERSION", "1.0.0")
        },
        "model": {
            "name": os.environ.get("MODEL_NAME", "deepgaze2"),
            "device_type": os.environ.get("DEVICE_TYPE", "cpu")
        }
    }
    return config