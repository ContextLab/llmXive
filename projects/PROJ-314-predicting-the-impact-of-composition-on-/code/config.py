import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import logger from the package root
try:
    from code import logger as package_logger
    logger = package_logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
CONFIG = {}

def load_environment():
    """Load environment variables from .env file if it exists."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        logger.info(f"Loaded environment from {ENV_FILE}")
    else:
        logger.warning(f".env file not found at {ENV_FILE}")

def initialize_config():
    """Initialize configuration from environment variables."""
    load_environment()
    
    # Core settings
    CONFIG['MEMORY_LIMIT_GB'] = float(os.getenv('MEMORY_LIMIT_GB', '7.0'))
    CONFIG['DATA_DIR'] = PROJECT_ROOT / "data"
    CONFIG['CODE_DIR'] = PROJECT_ROOT / "code"
    CONFIG['LOGS_DIR'] = PROJECT_ROOT / "logs"
    
    # API Keys
    CONFIG['MP_API_KEY'] = os.getenv('MP_API_KEY', '')
    
    # Data Sources
    CONFIG['NIST_URL'] = os.getenv('NIST_URL', '')
    CONFIG['ARXIV_QUERY'] = os.getenv('ARXIV_QUERY', 'all:ceramic AND all:weibull')
    
    logger.info("Configuration initialized.")
    return CONFIG

def get_config_value(key: str) -> Optional[str]:
    """Get a configuration value by key."""
    return CONFIG.get(key)

def get_int_config(key: str, default: int = 0) -> int:
    """Get an integer configuration value."""
    val = CONFIG.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def get_float_config(key: str, default: float = 0.0) -> float:
    """Get a float configuration value."""
    val = CONFIG.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def get_bool_config(key: str, default: bool = False) -> bool:
    """Get a boolean configuration value."""
    val = CONFIG.get(key)
    if val is None:
        return default
    return str(val).lower() in ('true', '1', 'yes')

def get_api_key(service: str) -> str:
    """Get API key for a specific service."""
    key_map = {
        'materials_project': 'MP_API_KEY',
    }
    env_key = key_map.get(service.lower())
    if not env_key:
        return ''
    return os.getenv(env_key, '')

def get_data_source_url(source: str) -> str:
    """Get data source URL."""
    url_map = {
        'nist': 'NIST_URL',
    }
    env_key = url_map.get(source.lower())
    if not env_key:
        return ''
    return os.getenv(env_key, '')

def get_memory_limit() -> float:
    """Get the memory limit in GB."""
    return CONFIG.get('MEMORY_LIMIT_GB', 7.0)

def get_project_config() -> Dict[str, Any]:
    """Get the full project configuration."""
    return CONFIG.copy()

# Initialize config on import
initialize_config()
