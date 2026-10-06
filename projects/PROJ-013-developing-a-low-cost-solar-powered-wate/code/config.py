import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils import get_project_root, ProjectError, setup_logging

logger = setup_logging(__name__)

class Config:
    def __init__(self):
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from environment or default values."""
        # Default NASA POWER key (can be overridden by .env)
        self._config['NASA_POWER_KEY'] = os.getenv('NASA_POWER_KEY', 'DEMO_KEY')
        
        # Add other configs here
        logger.info("Configuration loaded successfully")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

_config_instance = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config():
    global _config_instance
    _config_instance = Config()

def get_nasa_power_key() -> str:
    return get_config().get('NASA_POWER_KEY', 'DEMO_KEY')