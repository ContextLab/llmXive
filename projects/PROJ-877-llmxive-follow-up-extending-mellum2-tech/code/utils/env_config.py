"""
Environment configuration management for llmXive pipeline.

Handles .env file loading, Hugging Face token retrieval, and general
environment variable access with robust error handling.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    # This should be caught by requirements.txt, but fail loudly if missing
    raise ImportError(
        "python-dotenv is required. Please run: pip install python-dotenv"
    )

from utils.logging import get_logger

logger = get_logger(__name__)

# Default .env file location relative to project root
DEFAULT_ENV_FILE = ".env"

# Required environment variables for the pipeline
REQUIRED_VARS = [
    "HF_TOKEN",  # Hugging Face API token for dataset/model access
]

# Optional environment variables
OPTIONAL_VARS = [
    "HF_HOME",          # Custom path for HF cache
    "TRANSFORMERS_CACHE", # Custom path for transformers cache
    "CUDA_VISIBLE_DEVICES", # GPU visibility (default to CPU if not set)
    "PYTHONHASHSEED",   # For reproducibility
]

def load_environment(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, uses DEFAULT_ENV_FILE 
                 in the current working directory.
    
    Returns:
        bool: True if loading was successful, False otherwise.
    
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
    """
    if env_path is None:
        env_path = DEFAULT_ENV_FILE
    
    env_file = Path(env_path)
    
    if not env_file.exists():
        logger.warning(f"Environment file not found at {env_file}. "
                     "Proceeding with system environment variables only. "
                     "Create a .env file with HF_TOKEN if accessing gated datasets/models.")
        return False
    
    try:
        loaded = load_dotenv(env_file, override=True)
        if loaded:
            logger.info(f"Successfully loaded environment variables from {env_file}")
        else:
            logger.warning(f"No variables loaded from {env_file} (file may be empty)")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment from {env_file}: {e}")
        return False

def get_hf_token(required: bool = True) -> Optional[str]:
    """
    Retrieve the Hugging Face token from environment variables.
    
    This token is required for accessing gated datasets (e.g., codeparrot/github-code)
    and models (e.g., Mistral-7B).
    
    Args:
        required: If True, raises an error if the token is missing. 
                 If False, returns None.
    
    Returns:
        Optional[str]: The HF token string, or None if not found and required=False.
    
    Raises:
        ValueError: If required=True and the token is not found.
    """
    token = os.getenv("HF_TOKEN")
    
    if not token:
        if required:
            error_msg = (
                "Hugging Face token (HF_TOKEN) not found in environment variables. "
                "Please set it in your .env file or export it directly. "
                "Example: echo 'HF_TOKEN=your_token_here' >> .env\n"
                "You can get a token from https://huggingface.co/settings/tokens"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            logger.debug("HF_TOKEN not found, proceeding without it (may fail on gated resources)")
            return None
    
    # Validate token format (basic check)
    if not token.startswith("hf_"):
        logger.warning(f"HF_TOKEN does not appear to be a valid Hugging Face token format (should start with 'hf_')")
    
    # Mask token for logging
    masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
    logger.debug(f"HF_TOKEN loaded successfully (masked: {masked_token})")
    
    return token

def get_env_var(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable with optional default and validation.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if the variable is not set.
        required: If True, raises an error if the variable is missing and no default provided.
    
    Returns:
        Optional[str]: The value of the environment variable, or default if set.
    
    Raises:
        ValueError: If required=True and the variable is missing with no default.
    """
    value = os.getenv(var_name, default)
    
    if value is None and required:
        error_msg = f"Required environment variable '{var_name}' is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if value is not None:
        logger.debug(f"Loaded environment variable: {var_name}={value[:4]}...{value[-4:]}" 
                    if len(value) > 8 else f"Loaded environment variable: {var_name}={value}")
    
    return value

def validate_required_env_vars() -> Dict[str, str]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Dict[str, str]: A dictionary of missing required variables and their expected names.
                       Empty if all required variables are present.
    
    Raises:
        ValueError: If any required variables are missing.
    """
    missing = {}
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            missing[var] = "Required"
    
    if missing:
        error_msg = (
            "Missing required environment variables:\n" +
            "\n".join([f"  - {k}: {v}" for k, v in missing.items()]) +
            "\n\nPlease set these in your .env file or export them directly."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All required environment variables are present")
    return {}

def get_environment_summary() -> Dict[str, Any]:
    """
    Get a summary of the current environment configuration.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'hf_token_set': bool (whether HF_TOKEN is set)
            - 'hf_home': str or None
            - 'cuda_visible_devices': str or None
            - 'pythonhashseed': str or None
            - 'required_vars_present': bool
    """
    summary = {
        "hf_token_set": bool(os.getenv("HF_TOKEN")),
        "hf_home": os.getenv("HF_HOME"),
        "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
        "pythonhashseed": os.getenv("PYTHONHASHSEED"),
        "required_vars_present": all(os.getenv(var) for var in REQUIRED_VARS),
    }
    
    logger.debug(f"Environment summary: {summary}")
    return summary

def main():
    """
    Main entry point for environment configuration testing and validation.
    
    This function:
    1. Attempts to load .env file
    2. Validates required environment variables
    3. Prints a summary of the environment configuration
    """
    print("=== llmXive Environment Configuration Check ===\n")
    
    # Load environment
    env_file = Path(DEFAULT_ENV_FILE)
    if env_file.exists():
        print(f"Loading environment from: {env_file.absolute()}")
        load_environment(str(env_file))
    else:
        print(f"No .env file found at {env_file.absolute()}")
        print("Creating a template .env file...")
        template = """# Hugging Face API Token
# Get your token from: https://huggingface.co/settings/tokens
HF_TOKEN=

# Optional: Custom cache directories
# HF_HOME=/path/to/hf/cache
# TRANSFORMERS_CACHE=/path/to/transformers/cache

# Optional: GPU configuration
# CUDA_VISIBLE_DEVICES=0,1

# Optional: Reproducibility
# PYTHONHASHSEED=42
"""
        with open(env_file, "w") as f:
            f.write(template)
        print(f"Template .env file created at {env_file.absolute()}")
        print("Please edit the file and set your HF_TOKEN before running the pipeline.\n")
        return
    
    # Validate required variables
    try:
        validate_required_env_vars()
        print("\n✓ All required environment variables are set.")
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return
    
    # Print summary
    summary = get_environment_summary()
    print("\n--- Environment Summary ---")
    for key, value in summary.items():
        if key == "hf_token_set" and value:
            print(f"{key}: True (token present)")
        elif isinstance(value, str) and value:
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else value
            print(f"{key}: {masked}")
        else:
            print(f"{key}: {value}")
    
    print("\n=== Environment configuration complete ===")

if __name__ == "__main__":
    main()