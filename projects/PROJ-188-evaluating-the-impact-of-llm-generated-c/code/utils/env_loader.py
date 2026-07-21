import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
DEFAULT_HF_TOKEN_VAR = "HF_TOKEN"
DEFAULT_MODEL_PATH_VAR = "MODEL_PATH"

def load_env_vars(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to project root .env.
        
    Returns:
        Dictionary of loaded environment variables.
        
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
    """
    if env_path is None:
        env_path = DEFAULT_ENV_PATH
        
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                     "Using system environment variables only.")
        return {}
        
    # Load variables from .env file
    load_dotenv(env_path, override=True)
    
    # Return currently set variables
    return {
        key: value 
        for key, value in os.environ.items() 
        if key in [DEFAULT_HF_TOKEN_VAR, DEFAULT_MODEL_PATH_VAR]
    }

def get_model_path(var_name: str = DEFAULT_MODEL_PATH_VAR) -> Optional[str]:
    """
    Retrieve the model path from environment variables.
    
    Args:
        var_name: Name of the environment variable containing the model path.
        
    Returns:
        The model path string if set, None otherwise.
    """
    path = os.getenv(var_name)
    if path:
        logger.info(f"Model path loaded from {var_name}")
    else:
        logger.warning(f"Model path not found in environment variable {var_name}")
    return path

def validate_token(var_name: str = DEFAULT_HF_TOKEN_VAR) -> bool:
    """
    Validate that the HuggingFace token is present in the environment.
    
    Args:
        var_name: Name of the environment variable containing the HF token.
        
    Returns:
        True if the token is present and non-empty, False otherwise.
        
    Raises:
        RuntimeError: If the token is missing or empty (fail loudly).
    """
    token = os.getenv(var_name)
    if not token:
        error_msg = (
            f"HuggingFace token not found in environment variable '{var_name}'. "
            f"Please set HF_TOKEN in your .env file or system environment. "
            f"This is required for accessing gated models like CodeLlama."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    if not token.strip():
        error_msg = (
            f"HuggingFace token in '{var_name}' is empty. "
            f"Please provide a valid token."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    logger.info("HuggingFace token validated successfully")
    return True

def main():
    """
    Main entry point for testing environment loading.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Loading environment variables...")
    env_vars = load_env_vars()
    logger.info(f"Loaded variables: {list(env_vars.keys())}")
    
    if DEFAULT_HF_TOKEN_VAR in env_vars:
        try:
            validate_token()
            logger.info("✓ HuggingFace token is valid")
        except (RuntimeError, ValueError) as e:
            logger.error(f"✗ Token validation failed: {e}")
            return 1
    else:
        logger.warning("No HF token found in environment")
        
    model_path = get_model_path()
    if model_path:
        logger.info(f"✓ Model path configured: {model_path}")
    else:
        logger.warning("No model path configured - will use default HuggingFace paths")
        
    return 0

if __name__ == "__main__":
    exit(main())
