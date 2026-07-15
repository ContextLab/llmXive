"""
Environment configuration utilities for llmXive.

Handles loading and validating environment variables.
"""

import os
from typing import Optional, Tuple
from pathlib import Path

REQUIRED_ENV_VARS = [
    "DATA_SEED",
    "JOYAI_VL_MODEL_PATH",
    "YOLO_MODEL_PATH"
]

def get_required_env_vars() -> Tuple[bool, str]:
    """
    Check if all required environment variables are set.

    Returns:
        Tuple of (all_set, error_message).
    """
    missing = []
    for var in REQUIRED_ENV_VARS:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        return False, f"Missing required environment variables: {', '.join(missing)}"
    return True, ""

def validate_environment() -> bool:
    """
    Validate the environment configuration.

    Returns:
        True if environment is valid, False otherwise.
    """
    is_valid, _ = get_required_env_vars()
    return is_valid

def load_environment_config() -> None:
    """
    Load environment configuration from .env file if it exists.
    """
    env_file = Path(".env")
    if env_file.exists():
        # Simple .env parser
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

def setup_environment() -> None:
    """
    Set up the environment by loading .env and validating.
    """
    load_environment_config()
    is_valid, error_msg = get_required_env_vars()
    if not is_valid:
        raise RuntimeError(error_msg)
