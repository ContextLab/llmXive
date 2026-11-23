"""
Environment configuration utilities.
Provides functions for loading and validating environment variables.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

def get_logger(name: str = "env_config") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file. If None, uses default location.
        
    Returns:
        True if .env was loaded successfully, False otherwise.
    """
    logger = get_logger()
    
    if env_path is None:
        # Try to find .env in project root
        project_root = Path.cwd()
        env_path = project_root / ".env"
        
    if env_path.exists():
        result = load_dotenv(dotenv_path=env_path)
        if result:
            logger.info(f"Loaded environment from {env_path}")
            return True
        else:
            logger.warning(f"Failed to load environment from {env_path}")
            return False
    else:
        logger.info(f"No .env file found at {env_path}")
        return False

def get_hf_token() -> Optional[str]:
    """
    Get Hugging Face token from environment.
    
    Returns:
        HF token string or None if not set.
    """
    return os.environ.get("HF_TOKEN")

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not set.
        
    Returns:
        Environment variable value or default.
    """
    return os.environ.get(var_name, default)

def validate_required_env_vars(required_vars: list) -> None:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of environment variable names that must be set.
        
    Raises:
        ValueError: If any required environment variable is missing.
    """
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please set them in your .env file or export them in your shell."
        )

def get_environment_summary() -> Dict[str, Any]:
    """
    Get a summary of the current environment configuration.
    
    Returns:
        Dictionary with environment variable status.
    """
    return {
        "hf_token_set": bool(os.environ.get("HF_TOKEN")),
        "hf_dataset_name": os.environ.get("HF_DATASET_NAME", "not set"),
        "project_root": os.environ.get("PROJECT_ROOT", "not set"),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}"
    }

def main():
    """
    Main entry point for environment configuration module.
    Demonstrates environment loading and validation.
    """
    logger = get_logger()
    
    # Load environment
    load_environment()
    
    # Validate required variables
    required = ["HF_TOKEN"]
    try:
        validate_required_env_vars(required)
        logger.info("All required environment variables are set.")
    except ValueError as e:
        logger.warning(str(e))
    
    # Print summary
    summary = get_environment_summary()
    logger.info(f"Environment summary: {summary}")

if __name__ == "__main__":
    main()
