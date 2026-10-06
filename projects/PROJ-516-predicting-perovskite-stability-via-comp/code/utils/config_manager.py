import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / 'config.yaml'
ENV_PATH = Path(__file__).parent.parent.parent / '.env'

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """Load environment variables from a .env file."""
    if env_path is None:
        env_path = ENV_PATH
    
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}")
        return False
    
    logger.info(f"Loading environment from {env_path}")
    return load_dotenv(env_path)

def get_api_key(service_name: str) -> Optional[str]:
    """Retrieve an API key from environment variables."""
    key_var = f"{service_name.upper()}_API_KEY"
    key = os.getenv(key_var)
    if not key:
        logger.warning(f"API key not found for {service_name} (env var: {key_var})")
    return key

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = CONFIG_PATH
    
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML config: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading config: {e}")

def validate_environment(required_keys: List[str]) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_keys: List of environment variable names that must be present.
    
    Returns:
        True if all keys are present, False otherwise.
    """
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False
    
    logger.info("Environment validation passed.")
    return True

def main():
    """Test the config manager."""
    logger.info("Testing config manager...")
    load_dotenv_file()
    config = load_config()
    logger.info(f"Config: {config}")
    
    # Example validation
    if validate_environment(['NREL_API_KEY']):
        logger.info("NREL API Key found.")
    else:
        logger.warning("NREL API Key missing (expected in test environment).")

if __name__ == '__main__':
    main()
