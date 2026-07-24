"""
Environment variable loading utilities for HuggingFace token and model paths.

This module provides functions to load, validate, and retrieve environment variables
required for model access, specifically the HuggingFace token and custom model paths.

Dependencies:
- python-dotenv (optional, for .env file support)
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_VARS = {
    'HF_TOKEN': 'HuggingFace API token for model access',
    'HF_MODEL_PATH': 'Path to HuggingFace model cache (optional, defaults to HF_HOME)',
    'TRANSFORMERS_CACHE': 'Transformers cache directory (optional)',
}

def load_env_vars(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to .env file. Defaults to project root .env.
    
    Returns:
        Dictionary of loaded environment variables.
    
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
    """
    env_dict = {}
    
    if env_path is None:
        # Default to .env in project root
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / '.env'
    
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        try:
            # Try to load using python-dotenv if available
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_path)
                logger.info("Successfully loaded .env file using python-dotenv")
            except ImportError:
                logger.warning("python-dotenv not installed. Manual .env parsing not implemented.")
                logger.warning("Please ensure environment variables are set in your shell or system.")
                # Fallback: manual parsing (simple key=value)
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            env_dict[key] = value
                            os.environ[key] = value
                logger.info(f"Manually loaded {len(env_dict)} variables from .env")
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            raise
    else:
        logger.info(f"No .env file found at {env_path}. Using system environment variables.")
    
    return env_dict

def get_model_path() -> Optional[str]:
    """
    Get the HuggingFace model path from environment variables.
    
    Priority:
    1. HF_MODEL_PATH
    2. TRANSFORMERS_CACHE
    3. HF_HOME
    4. Default: ~/.cache/huggingface
    
    Returns:
        Path to model cache directory or None if not set.
    """
    model_path = os.getenv('HF_MODEL_PATH')
    
    if model_path:
        logger.info(f"Using HF_MODEL_PATH: {model_path}")
        return model_path
    
    # Fallback to TRANSFORMERS_CACHE
    transformers_cache = os.getenv('TRANSFORMERS_CACHE')
    if transformers_cache:
        logger.info(f"Using TRANSFORMERS_CACHE: {transformers_cache}")
        return transformers_cache
    
    # Fallback to HF_HOME
    hf_home = os.getenv('HF_HOME')
    if hf_home:
        logger.info(f"Using HF_HOME: {hf_home}")
        return hf_home
    
    # Default path
    default_path = str(Path.home() / '.cache' / 'huggingface')
    logger.info(f"Using default HF cache path: {default_path}")
    return default_path

def validate_token(token: Optional[str] = None) -> bool:
    """
    Validate the HuggingFace token.
    
    Args:
        token: Token string. If None, reads from HF_TOKEN env var.
    
    Returns:
        True if token is present and non-empty, False otherwise.
    
    Raises:
        ValueError: If token is missing or empty.
    """
    if token is None:
        token = os.getenv('HF_TOKEN')
    
    if not token or not token.strip():
        error_msg = "HuggingFace token (HF_TOKEN) is not set. Please set it via environment variable or .env file."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Basic format validation (HF tokens typically start with 'hf_')
    token = token.strip()
    if not token.startswith('hf_'):
        logger.warning(f"Token does not start with 'hf_'. This may indicate an invalid token format.")
    
    logger.info("HuggingFace token validated successfully")
    return True

def ensure_required_vars() -> Dict[str, str]:
    """
    Ensure all required environment variables are set.
    
    Returns:
        Dictionary of required variables and their values.
    
    Raises:
        ValueError: If any required variable is missing.
    """
    missing_vars = []
    env_vars = {}
    
    for var_name, description in REQUIRED_VARS.items():
        value = os.getenv(var_name)
        if value:
            env_vars[var_name] = value
            logger.debug(f"Found required variable: {var_name}")
        else:
            # Some vars are optional
            if var_name == 'HF_TOKEN':
                missing_vars.append(f"{var_name} ({description})")
            else:
                logger.info(f"Optional variable {var_name} not set, using default")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All required environment variables are set")
    return env_vars

def main():
    """
    Main function to demonstrate environment variable loading and validation.
    """
    print("=== Environment Variable Loader Test ===")
    
    # Load .env if exists
    load_env_vars()
    
    # Ensure required vars
    try:
        env_vars = ensure_required_vars()
        print(f"✓ Required variables found: {list(env_vars.keys())}")
    except ValueError as e:
        print(f"✗ Missing required variables: {e}")
        return 1
    
    # Validate token
    try:
        validate_token()
        print("✓ Token validated successfully")
    except ValueError as e:
        print(f"✗ Token validation failed: {e}")
        return 1
    
    # Get model path
    model_path = get_model_path()
    print(f"✓ Model path: {model_path}")
    
    # Check if path exists
    if model_path:
        path_obj = Path(model_path)
        if path_obj.exists():
            print(f"✓ Model path exists: {path_obj}")
        else:
            print(f"⚠ Model path does not exist (will be created on first use): {path_obj}")
    
    print("=== Test Complete ===")
    return 0

if __name__ == "__main__":
    exit(main())