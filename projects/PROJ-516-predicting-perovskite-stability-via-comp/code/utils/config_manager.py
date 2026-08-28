"""
Configuration management module for handling environment variables and API keys.
Provides secure loading of .env files and retrieval of configuration values.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in the 
                  code directory (project root relative to code/).
    
    Returns:
        bool: True if file was loaded successfully, False otherwise.
    
    Raises:
        ConfigError: If the file exists but cannot be read.
    """
    if env_path is None:
        # Default to .env in the same directory as this module's parent (code/)
        env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "API keys will not be available. "
                     "Please copy code/.env.example to code/.env and fill in values.")
        return False
    
    try:
        # Parse the .env file manually to avoid external dependencies like python-dotenv
        # if we want to keep dependencies minimal, or use a simple parser.
        # However, standard practice is to use python-dotenv. Let's implement a simple parser
        # to ensure we don't add a new dependency if not strictly necessary, 
        # but python-dotenv is standard for this. 
        # Given T002 (requirements.txt) is done, let's assume we can use 'python-dotenv' 
        # or implement a simple one. To be safe and robust without adding deps if not listed:
        # We will implement a simple parser.
        
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                os.environ[key] = value
        
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to load .env file from {env_path}: {e}")
        raise ConfigError(f"Could not load .env file: {e}")

def get_api_key(key_name: str, required: bool = True) -> Optional[str]:
    """
    Retrieve an API key from the environment.
    
    Args:
        key_name: The name of the environment variable (e.g., 'MP_API_KEY').
        required: If True, raises ConfigError if the key is missing.
    
    Returns:
        The API key string, or None if not found and not required.
    
    Raises:
        ConfigError: If required=True and the key is not found.
    """
    value = os.environ.get(key_name)
    
    if value is None:
        if required:
            raise ConfigError(
                f"Required API key '{key_name}' is missing. "
                f"Please ensure it is set in the .env file or environment variables."
            )
        return None
    
    return value

def validate_environment(required_keys: list[str]) -> Dict[str, bool]:
    """
    Validate that all required API keys are present in the environment.
    
    Args:
        required_keys: List of environment variable names that must be present.
    
    Returns:
        Dict mapping key names to their validation status (True if present).
    
    Raises:
        ConfigError: If any required key is missing.
    """
    status = {}
    missing = []
    
    for key in required_keys:
        if os.environ.get(key):
            status[key] = True
        else:
            status[key] = False
            missing.append(key)
    
    if missing:
        raise ConfigError(
            f"The following required API keys are missing: {', '.join(missing)}. "
            f"Please update your .env file."
        )
    
    logger.info("Environment validation passed.")
    return status
