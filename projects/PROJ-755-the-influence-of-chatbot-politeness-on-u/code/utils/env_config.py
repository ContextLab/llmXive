"""
Environment configuration management utilities.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv
import logging

logger = logging.getLogger(__name__)


class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass


def load_env_config(env_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment configuration from .env file.
    
    Args:
        env_file: Path to .env file (default: auto-detect)
        
    Returns:
        Dictionary of environment variables
    """
    if env_file is None:
        env_file = find_dotenv()
    
    if not env_file:
        logger.warning("No .env file found. Using system environment variables.")
        return {}
    
    load_dotenv(env_file)
    return dict(os.environ)


def get_hf_token() -> Optional[str]:
    """
    Get HuggingFace token from environment.
    
    Returns:
        HF token string or None if not found
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.warning("HF_TOKEN not found in environment variables.")
        return None
    return token


def validate_env_config(required_vars: list = None) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of required variable names
        
    Returns:
        True if all required variables are set
        
    Raises:
        EnvConfigError: If required variables are missing
    """
    if required_vars is None:
        required_vars = ["HF_TOKEN"]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise EnvConfigError(f"Missing required environment variables: {missing}")
    
    return True


def create_env_template(template_path: Path = None):
    """
    Create a .env.example template file.
    
    Args:
        template_path: Path to save template (default: .env.example)
    """
    if template_path is None:
        template_path = Path(".env.example")
    
    template_content = """# Environment Configuration Template
# Copy this file to .env and fill in your values

# HuggingFace API Token (required for dataset downloads)
HF_TOKEN=

# Optional: Other configuration
# LOG_LEVEL=INFO
# MAX_MEMORY_GB=7
"""
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    logger.info(f"Created environment template at {template_path}")


def ensure_env_file_exists():
    """
    Ensure .env file exists, creating template if not.
    """
    env_path = Path(".env")
    if not env_path.exists():
        logger.info(".env file not found. Creating template...")
        create_env_template()
        logger.info("Please copy .env.example to .env and fill in your values.")
        return False
    return True