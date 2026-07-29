"""
Environment configuration management for llmXive pipeline.
Handles .env file loading, Hugging Face token retrieval, and environment validation.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from utils.logging import get_logger

logger = get_logger(__name__)

# Default .env file path
ENV_FILE_PATH = Path(".env")


def load_environment(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to the .env file. Defaults to .env in project root.
    
    Returns:
        Dictionary of loaded environment variables.
    
    Raises:
        FileNotFoundError: If the specified env_path does not exist.
    """
    if env_path is None:
        env_path = ENV_FILE_PATH
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "Some features may require manual environment variable setup.")
        return {}
    
    loaded_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' not in line:
                    logger.warning(f"Skipping malformed line {line_num} in .env: {line}")
                    continue
                
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # Remove surrounding quotes if present
                if len(value) >= 2 and ((value.startswith('"') and value.endswith('"')) or 
                                       (value.startswith("'") and value.endswith("'"))):
                    value = value[1:-1]
                
                if key:
                    loaded_vars[key] = value
                    # Set in actual environment
                    os.environ[key] = value
                    
        logger.info(f"Successfully loaded {len(loaded_vars)} variables from {env_path}")
        return loaded_vars
    except Exception as e:
        logger.error(f"Error reading .env file at {env_path}: {e}")
        raise


def get_hf_token() -> str:
    """
    Retrieve the Hugging Face API token from environment variables.
    
    Priority:
    1. HUGGING_FACE_TOKEN (explicit variable)
    2. HF_TOKEN (standard HF variable)
    3. HuggingfaceToken (from .env)
    
    Returns:
        The Hugging Face token string.
    
    Raises:
        ValueError: If no token is found in any expected location.
    """
    token = (
        os.environ.get("HUGGING_FACE_TOKEN") or
        os.environ.get("HF_TOKEN") or
        os.environ.get("HuggingfaceToken")
    )
    
    if not token:
        error_msg = (
            "Hugging Face token not found. Please set one of the following environment variables:\n"
            "- HUGGING_FACE_TOKEN\n"
            "- HF_TOKEN\n"
            "- HuggingfaceToken\n"
            "Or create a .env file with HuggingfaceToken=your_token_here"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not token.startswith("hf_"):
        logger.warning("Token does not appear to be a valid Hugging Face token (missing 'hf_' prefix).")
    
    return token


def get_env_var(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable with optional default and required flag.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if variable is not set.
        required: If True, raise ValueError when variable is missing.
    
    Returns:
        The environment variable value or default.
    
    Raises:
        ValueError: If required=True and variable is not set.
    """
    value = os.environ.get(var_name, default)
    
    if value is None and required:
        error_msg = f"Required environment variable '{var_name}' is not set."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return value


def validate_required_env_vars(required_vars: list) -> bool:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names.
    
    Returns:
        True if all required variables are set, False otherwise.
    
    Raises:
        ValueError: If any required variable is missing.
    """
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        error_msg = (
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please ensure these are set in your .env file or system environment."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"All {len(required_vars)} required environment variables are set.")
    return True


def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.
    
    Returns:
        Dictionary containing environment status and key configuration details.
    """
    has_env_file = ENV_FILE_PATH.exists()
    hf_token_set = bool(os.environ.get("HUGGING_FACE_TOKEN") or 
                      os.environ.get("HF_TOKEN") or 
                      os.environ.get("HuggingfaceToken"))
    
    return {
        "env_file_exists": has_env_file,
        "hf_token_configured": hf_token_set,
        "loaded_vars_count": len([k for k in os.environ.keys() if k in 
                                ["HUGGING_FACE_TOKEN", "HF_TOKEN", "HuggingfaceToken",
                                 "RANDOM_SEED", "DATA_DIR", "CODE_DIR"]]),
        "python_path": os.environ.get("PYTHONPATH", "not set")
    }


def main():
    """
    Main entry point for environment configuration testing.
    """
    logger.info("=== Environment Configuration Check ===")
    
    # Load environment
    try:
        load_environment()
    except Exception as e:
        logger.error(f"Failed to load environment: {e}")
        return 1
    
    # Summary
    summary = get_environment_summary()
    logger.info(f"Environment Summary: {summary}")
    
    # Validate HF token specifically
    try:
        token = get_hf_token()
        logger.info("Hugging Face token: VALID (masked)")
    except ValueError as e:
        logger.warning(f"Hugging Face token: MISSING - {e}")
    
    return 0


if __name__ == "__main__":
    exit(main())
