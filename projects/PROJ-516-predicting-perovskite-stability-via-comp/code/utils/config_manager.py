"""
Configuration management for API keys and environment variables.

This module handles the loading and validation of environment variables
required for external data sources (Materials Project, NREL).
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

def load_dotenv_file(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file.
    
    This is a lightweight implementation to avoid adding 'python-dotenv'
    as a dependency unless strictly necessary, though it can be added
    if the project requirements allow.
    
    Args:
        env_path: Path to the .env file. Defaults to project root .env.
    """
    if env_path is None:
        # Look for .env in the code directory (project root relative to code/)
        # Assuming project structure: PROJ_ROOT/
        #   code/
        #     .env
        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / ".env"

    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                       "API keys may be missing. Use .env.example as a template.")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                os.environ[key] = value
    logger.info(f"Loaded environment variables from {env_path}")

def get_api_key(provider: str) -> str:
    """
    Retrieve an API key from the environment.
    
    Args:
        provider: The name of the provider (e.g., 'materials_project', 'nrel').
    
    Returns:
        The API key string.
    
    Raises:
        ConfigError: If the key is not found in the environment.
    """
    env_vars = {
        "materials_project": "MATERIALS_PROJECT_API_KEY",
        "nrel": "NREL_API_KEY",
    }
    
    env_key = env_vars.get(provider.lower())
    if not env_key:
        raise ConfigError(f"Unknown provider: {provider}. Supported: {list(env_vars.keys())}")
    
    value = os.environ.get(env_key)
    if not value:
        raise ConfigError(
            f"Missing required environment variable '{env_key}'. "
            f"Please configure it in your .env file."
        )
    
    return value

def validate_environment() -> Dict[str, bool]:
    """
    Validate that all required API keys are present.
    
    Returns:
        A dictionary mapping provider names to boolean status (True if valid).
    """
    results = {}
    for provider in ["materials_project", "nrel"]:
        try:
            get_api_key(provider)
            results[provider] = True
            logger.debug(f"API key for {provider} is configured.")
        except ConfigError:
            results[provider] = False
            logger.warning(f"API key for {provider} is NOT configured.")
    
    return results
