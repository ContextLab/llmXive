"""
Environment configuration management for the llmXive project.

This module handles the loading and validation of environment variables,
including API keys for external services like Materials Project.
"""
import os
from pathlib import Path
from typing import Optional
import logging

# Try to import dotenv, but handle gracefully if not installed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("python-dotenv not installed. Environment variables must be set in the system.")

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_environment(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Optional path to the .env file. If None, looks for .env in the project root.
        
    Returns:
        True if loaded successfully, False if not found or dotenv unavailable.
        
    Raises:
        ConfigError: If the file exists but cannot be parsed.
    """
    if not DOTENV_AVAILABLE:
        logger.warning("python-dotenv is not installed. Skipping .env file loading.")
        return False

    if env_path is None:
        # Determine project root (assuming this file is in src/config/)
        # Project root is 3 levels up from src/config/env_config.py
        base_dir = Path(__file__).resolve().parent.parent.parent
        env_path = base_dir / ".env"

    if not env_path.exists():
        logger.info(f"No .env file found at {env_path}. Using system environment variables.")
        return False

    logger.info(f"Loading environment from {env_path}")
    success = load_dotenv(env_path)
    
    if not success:
        logger.warning("Failed to load .env file (file might be empty or malformed).")
        return False
    
    return True

def get_required_env_var(name: str, description: str = "") -> str:
    """
    Retrieve a required environment variable.
    
    Args:
        name: The name of the environment variable.
        description: A human-readable description of what the variable is for.
        
    Returns:
        The value of the environment variable.
        
    Raises:
        ConfigError: If the variable is not set or is empty.
    """
    value = os.getenv(name)
    if not value:
        hint = f" ({description})" if description else ""
        raise ConfigError(
            f"Missing required environment variable: {name}{hint}. "
            f"Please set it in your .env file or system environment."
        )
    return value

def get_optional_env_var(name: str, default: str = "") -> str:
    """
    Retrieve an optional environment variable.
    
    Args:
        name: The name of the environment variable.
        default: The default value if the variable is not set.
        
    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(name, default)

class ProjectConfig:
    """
    Centralized configuration class for the project.
    Loads and validates all necessary environment variables on instantiation.
    """
    def __init__(self, load_env: bool = True):
        """
        Initialize the configuration.
        
        Args:
            load_env: If True, attempt to load from .env file.
        """
        if load_env:
            load_environment()
        
        # Load and validate API keys
        self.materials_project_api_key = get_required_env_var(
            "MATERIALS_PROJECT_API_KEY",
            "Required for fetching data from Materials Project"
        )
        
        self.nist_api_token = get_optional_env_var("NIST_API_TOKEN")
        self.arxiv_user_agent = get_optional_env_var(
            "ARXIV_USER_AGENT",
            default="llmXive-research-implementer/1.0"
        )
        
        # Logging configuration
        log_level = get_optional_env_var("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Random seed
        self.random_seed = int(get_optional_env_var("RANDOM_SEED", "42"))
        
        logger.info("Project configuration loaded successfully.")

# Singleton instance for easy access
_config_instance = None

def get_config() -> ProjectConfig:
    """
    Get the singleton configuration instance.
    
    Returns:
        The ProjectConfig instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig()
    return _config_instance
