"""
Environment configuration management for llmXive project.

Handles .env file loading, API key validation, and secure retrieval of
environment variables required for data fetching and external service access.
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from dotenv import load_dotenv
from .logging_config import get_logger

logger = get_logger(__name__)

# Default path for .env file relative to project root
DEFAULT_ENV_PATH = Path(".env")

# Required API keys for external data sources
REQUIRED_KEYS = [
    "HUGGINGFACE_TOKEN",  # For Hugging Face datasets
    "NCBI_API_KEY",        # For NCBI SRA/Entrez access
]

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. Defaults to project root .env.
        
    Returns:
        True if file was loaded successfully, False otherwise.
    """
    if env_path is None:
        env_path = DEFAULT_ENV_PATH
    
    # Convert to absolute path if relative
    if not env_path.is_absolute():
        # Assume project root is parent of code/
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / env_path
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "Some API keys may be missing. "
                     "Create a .env file with required keys if needed.")
        return False
    
    try:
        loaded = load_dotenv(dotenv_path=env_path)
        if loaded:
            logger.info(f"Successfully loaded environment from {env_path}")
        else:
            logger.debug(f"No environment variables loaded from {env_path}")
        return loaded
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False

def validate_api_keys(required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate that required API keys are present in the environment.
    
    Args:
        required_keys: List of key names to check. Defaults to REQUIRED_KEYS.
        
    Returns:
        Dict with 'valid' (bool), 'missing' (list), and 'present' (list).
    """
    if required_keys is None:
        required_keys = REQUIRED_KEYS
    
    missing = []
    present = []
    
    for key in required_keys:
        value = os.getenv(key)
        if value is None or value.strip() == "":
            missing.append(key)
        else:
            present.append(key)
            # Log that key is present (without revealing value)
            logger.debug(f"API key '{key}' is configured")
    
    result = {
        "valid": len(missing) == 0,
        "missing": missing,
        "present": present,
        "required": required_keys
    }
    
    if not result["valid"]:
        logger.warning(f"Missing required API keys: {missing}")
        logger.info("To fix: Add these keys to your .env file or export them as environment variables")
    
    return result

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable with optional default and validation.
    
    Args:
        key: Environment variable name.
        default: Default value if key is not set.
        required: If True, raise ValueError when key is missing.
        
    Returns:
        The environment variable value or default.
        
    Raises:
        ValueError: If required=True and key is not set.
    """
    value = os.getenv(key, default)
    
    if required and (value is None or value.strip() == ""):
        raise ValueError(f"Required environment variable '{key}' is not set. "
                       f"Please add it to your .env file or export it.")
    
    return value

def setup_environment(env_path: Optional[Path] = None, 
                    validate_required: bool = True) -> Dict[str, Any]:
    """
    Complete environment setup: load .env file and validate required keys.
    
    Args:
        env_path: Optional path to .env file.
        validate_required: If True, validate that all REQUIRED_KEYS are present.
        
    Returns:
        Dict with setup status, validation results, and any errors.
    """
    result = {
        "env_loaded": False,
        "env_path": str(env_path) if env_path else "default (.env)",
        "validation": None,
        "errors": [],
        "warnings": []
    }
    
    # Load .env file
    result["env_loaded"] = load_dotenv_file(env_path)
    
    if not result["env_loaded"] and validate_required:
        result["warnings"].append(
            "No .env file found. If you need API keys for data fetching, "
            "create a .env file in the project root."
        )
    
    # Validate required keys if requested
    if validate_required:
        result["validation"] = validate_api_keys()
        if not result["validation"]["valid"]:
            result["errors"].append(
                f"Missing required API keys: {result['validation']['missing']}"
            )
    
    # Log summary
    if result["env_loaded"]:
        logger.info("Environment setup complete")
    else:
        logger.info("Environment setup complete (no .env file found)")
    
    if result["validation"] and not result["validation"]["valid"]:
        logger.warning("Some required API keys are missing")
    
    return result

def get_huggingface_token() -> Optional[str]:
    """
    Get Hugging Face API token for dataset access.
    
    Returns:
        The token string or None if not configured.
    """
    return get_env_var("HUGGINGFACE_TOKEN", required=False)

def get_ncbi_api_key() -> Optional[str]:
    """
    Get NCBI API key for SRA/Entrez access.
    
    Returns:
        The API key string or None if not configured.
    """
    return get_env_var("NCBI_API_KEY", required=False)

def get_random_seed() -> int:
    """
    Get random seed for reproducibility.
    
    Returns:
        Random seed as integer (defaults to 42 if not set).
    """
    seed_str = get_env_var("RANDOM_SEED", default="42")
    try:
        return int(seed_str)
    except ValueError:
        logger.warning(f"Invalid RANDOM_SEED value '{seed_str}', using default 42")
        return 42

def get_max_workers() -> int:
    """
    Get maximum number of workers for parallel processing.
    
    Returns:
        Number of workers (defaults to 4 if not set).
    """
    workers_str = get_env_var("MAX_WORKERS", default="4")
    try:
        return max(1, int(workers_str))
    except ValueError:
        logger.warning(f"Invalid MAX_WORKERS value '{workers_str}', using default 4")
        return 4

def get_timeout_seconds() -> int:
    """
    Get timeout for network requests in seconds.
    
    Returns:
        Timeout value (defaults to 60 if not set).
    """
    timeout_str = get_env_var("REQUEST_TIMEOUT", default="60")
    try:
        return max(10, int(timeout_str))
    except ValueError:
        logger.warning(f"Invalid REQUEST_TIMEOUT value '{timeout_str}', using default 60")
        return 60

def get_cache_dir() -> Path:
    """
    Get directory for caching downloaded data.
    
    Returns:
        Path to cache directory (defaults to data/cache).
    """
    cache_path = get_env_var("CACHE_DIR", default="data/cache")
    return Path(cache_path)

# Initialize environment on module import
_setup_result = setup_environment(validate_required=False)

if __name__ == "__main__":
    # Test the environment setup
    print("=== Environment Configuration Test ===")
    result = setup_environment(validate_required=True)
    print(f"Env loaded: {result['env_loaded']}")
    print(f"Env path: {result['env_path']}")
    
    if result['validation']:
        print(f"Validation valid: {result['validation']['valid']}")
        if result['validation']['missing']:
            print(f"Missing keys: {result['validation']['missing']}")
        if result['validation']['present']:
            print(f"Present keys: {result['validation']['present']}")
    
    if result['errors']:
        print(f"Errors: {result['errors']}")
    if result['warnings']:
        print(f"Warnings: {result['warnings']}")
    
    print("\n=== Available Configuration Values ===")
    print(f"Random Seed: {get_random_seed()}")
    print(f"Max Workers: {get_max_workers()}")
    print(f"Request Timeout: {get_timeout_seconds()}s")
    print(f"Cache Dir: {get_cache_dir()}")
    
    hf_token = get_huggingface_token()
    print(f"HuggingFace Token: {'Set' if hf_token else 'Not set'}")
    
    ncbi_key = get_ncbi_api_key()
    print(f"NCBI API Key: {'Set' if ncbi_key else 'Not set'}")
