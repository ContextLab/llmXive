import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Constants for environment variable names
HF_TOKEN_ENV = "HF_TOKEN"
TINYLLAMA_PATH_ENV = "TINYLLAMA_MODEL_PATH"
CODELLAMA_PATH_ENV = "CODELLAMA_MODEL_PATH"

# Default model paths if env vars are missing (used only if not set)
DEFAULT_TINYLLAMA_PATH = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEFAULT_CODELLAMA_PATH = "codellama/CodeLlama-7b-Instruct-hf"

def load_env_vars() -> Dict[str, str]:
    """
    Load required environment variables for the project.
    
    Returns:
        Dict[str, str]: Dictionary of loaded environment variables.
    
    Raises:
        ValueError: If required variables are missing.
    """
    required_vars = [HF_TOKEN_ENV]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please set {HF_TOKEN_ENV} in your environment."
        )
    
    loaded = {}
    for var in required_vars:
        loaded[var] = os.getenv(var)
        logger.info(f"Loaded environment variable: {var}")
    
    # Optional model paths
    if os.getenv(TINYLLAMA_PATH_ENV):
        loaded[TINYLLAMA_PATH_ENV] = os.getenv(TINYLLAMA_PATH_ENV)
        logger.info(f"Loaded custom TinyLlama path: {loaded[TINYLLAMA_PATH_ENV]}")
    else:
        loaded[TINYLLAMA_PATH_ENV] = DEFAULT_TINYLLAMA_PATH
        logger.info(f"Using default TinyLlama path: {DEFAULT_TINYLLAMA_PATH}")
        
    if os.getenv(CODELLAMA_PATH_ENV):
        loaded[CODELLAMA_PATH_ENV] = os.getenv(CODELLAMA_PATH_ENV)
        logger.info(f"Loaded custom CodeLlama path: {loaded[CODELLAMA_PATH_ENV]}")
    else:
        loaded[CODELLAMA_PATH_ENV] = DEFAULT_CODELLAMA_PATH
        logger.info(f"Using default CodeLlama path: {DEFAULT_CODELLAMA_PATH}")
    
    return loaded

def get_model_path(model_name: str) -> str:
    """
    Get the model path for a specific model.
    
    Args:
        model_name (str): Name of the model ('tinyllama' or 'codellama').
        
    Returns:
        str: Path to the model.
        
    Raises:
        ValueError: If model_name is invalid.
    """
    env_vars = load_env_vars()
    
    if model_name.lower() == "tinyllama":
        return env_vars[TINYLLAMA_PATH_ENV]
    elif model_name.lower() == "codellama":
        return env_vars[CODELLAMA_PATH_ENV]
    else:
        raise ValueError(f"Invalid model name: {model_name}. Use 'tinyllama' or 'codellama'.")

def validate_token(token: Optional[str] = None) -> bool:
    """
    Validate the HuggingFace token.
    
    Args:
        token (Optional[str]): Token to validate. If None, uses HF_TOKEN env var.
        
    Returns:
        bool: True if token is valid (non-empty), False otherwise.
    """
    if token is None:
        token = os.getenv(HF_TOKEN_ENV)
    
    if not token or not isinstance(token, str) or len(token.strip()) == 0:
        logger.error("HuggingFace token is missing or invalid.")
        return False
    
    # Basic format check (HF tokens are typically 40+ characters)
    if len(token) < 20:
        logger.warning("HuggingFace token seems unusually short.")
        return False
        
    logger.info("HuggingFace token validated successfully.")
    return True

def ensure_required_vars() -> None:
    """
    Ensure all required environment variables are set and valid.
    
    Raises:
        RuntimeError: If any required variable is missing or invalid.
    """
    try:
        env_vars = load_env_vars()
        if not validate_token(env_vars.get(HF_TOKEN_ENV)):
            raise RuntimeError("HuggingFace token validation failed.")
        logger.info("All required environment variables are set and valid.")
    except ValueError as e:
        raise RuntimeError(f"Environment variable error: {e}")

def main():
    """
    Main entry point for testing environment variable loading.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        ensure_required_vars()
        print("Environment variables loaded successfully.")
        print(f"TinyLlama path: {get_model_path('tinyllama')}")
        print(f"CodeLlama path: {get_model_path('codellama')}")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
