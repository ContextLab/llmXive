"""
Environment configuration and validation for the llmXive pipeline.

This module handles the loading and validation of critical environment variables
required for model execution and data reproducibility.
"""
import os
from typing import Optional, Tuple
from pathlib import Path

# Constants for required environment variables
ENV_MODEL_PATH = "JOYAI_VL_MODEL_PATH"
ENV_DATA_SEED = "DATA_SEED"

def get_required_env_vars() -> Tuple[str, str]:
    """
    Returns the names of the required environment variables.
    
    Returns:
        Tuple containing (model_path_var_name, data_seed_var_name)
    """
    return ENV_MODEL_PATH, ENV_DATA_SEED

def validate_environment() -> Tuple[bool, str]:
    """
    Validates that all required environment variables are set and valid.
    
    Checks:
        1. JOYAI_VL_MODEL_PATH is set and points to an existing directory.
        2. DATA_SEED is set and is a valid integer.
    
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty string.
    """
    model_path_var, seed_var = get_required_env_vars()
    
    # Check Model Path
    model_path = os.getenv(model_path_var)
    if not model_path:
        return False, f"Environment variable '{model_path_var}' is not set."
    
    if not Path(model_path).exists():
        return False, f"Model path '{model_path}' does not exist."
    
    if not Path(model_path).is_dir():
        return False, f"Model path '{model_path}' is not a directory."

    # Check Data Seed
    seed_str = os.getenv(seed_var)
    if not seed_str:
        return False, f"Environment variable '{seed_var}' is not set."
    
    try:
        int(seed_str)
    except ValueError:
        return False, f"Environment variable '{seed_var}' must be a valid integer, got: '{seed_str}'"
    
    return True, ""

def load_environment_config() -> dict:
    """
    Loads the environment configuration into a dictionary.
    
    This function assumes the environment has already been validated
    (or that the caller handles the exception).
    
    Returns:
        dict: A dictionary containing 'model_path' and 'data_seed'.
    
    Raises:
        ValueError: If validation fails.
    """
    is_valid, error_msg = validate_environment()
    if not is_valid:
        raise ValueError(error_msg)
    
    return {
        "model_path": os.getenv(ENV_MODEL_PATH),
        "data_seed": int(os.getenv(ENV_DATA_SEED))
    }

def setup_environment() -> None:
    """
    Validates the environment and prints status.
    
    This is a convenience function for CLI entry points to ensure
    the environment is ready before proceeding.
    """
    is_valid, error_msg = validate_environment()
    if not is_valid:
        print(f"ERROR: Environment configuration invalid.")
        print(f"Reason: {error_msg}")
        raise SystemExit(1)
    
    config = load_environment_config()
    print(f"Environment OK.")
    print(f"  Model Path: {config['model_path']}")
    print(f"  Data Seed: {config['data_seed']}")
