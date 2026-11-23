"""
Environment Variable Management Module.

This module handles the loading and validation of environment variables
required for the pipeline, specifically the OPENNEURO_API_KEY.

It provides a centralized way to access configuration without hardcoding
secrets or paths.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Get the project root directory.
    Defaults to the parent of the 'code' directory if not set.
    """
    root = os.getenv("PROJECT_ROOT")
    if root:
        return Path(root)
    # Fallback: assume code/ is at root/code/
    return Path(__file__).resolve().parent.parent

def get_openneuro_api_key() -> Optional[str]:
    """
    Retrieve the OpenNeuro API key from environment variables.
    
    Returns:
        The API key string or None if not found.
    """
    return os.getenv("OPENNEURO_API_KEY")

def get_path(var_name: str, default: Optional[str] = None) -> Optional[Path]:
    """
    Retrieve a path from an environment variable.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not set.
        
    Returns:
        Path object or None.
    """
    val = os.getenv(var_name, default)
    if val:
        return Path(val)
    return None

def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        The path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config() -> Dict[str, Any]:
    """
    Load configuration from code/config.yaml if it exists.
    
    Returns:
        Dictionary of configuration values.
    """
    import yaml
    config_path = get_project_root() / "code" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if valid, False otherwise.
    """
    required_vars = ["OPENNEURO_API_KEY"]
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("Please set them in your shell or .env file.")
        return False
    return True

def main():
    """Main entry point for environment validation."""
    if validate_environment():
        logger.info("Environment validation successful.")
    else:
        logger.warning("Environment validation failed.")

if __name__ == "__main__":
    main()
