import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TolerantDict(dict):
    """A dictionary that tolerates missing keys gracefully."""
    def __missing__(self, key):
        return None

class AppConfig:
    """Configuration manager with tolerant access patterns."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or TolerantDict()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with nested key support."""
        if '.' in key:
            keys = key.split('.')
            value = self._config
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, TolerantDict())
                else:
                    return default
            return value if value is not None else default
        return self._config.get(key, default)
    
    def __getitem__(self, key):
        return self._config.get(key)
    
    def __contains__(self, key):
        return key in self._config

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f) or {}
            return AppConfig(config_dict)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return AppConfig()
    else:
        logger.info(f"No config file found at {config_path}, using defaults")
        return AppConfig()

def setup_logging(config: Optional[AppConfig] = None) -> logging.Logger:
    """Setup logging based on configuration."""
    level = logging.INFO
    if config:
        log_level = config.get('logging.level', 'INFO')
        if log_level == 'DEBUG':
            level = logging.DEBUG
        elif log_level == 'WARNING':
            level = logging.WARNING
        elif log_level == 'ERROR':
            level = logging.ERROR
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_seed(config: Optional[AppConfig] = None) -> int:
    """Get random seed from configuration."""
    if config:
        seed = config.get('random.seed', 42)
        return int(seed)
    return 42

def main():
    """Main entry point for config module (testing purposes)."""
    config = load_config()
    logger.info("Configuration loaded successfully")
    logger.info(f"Base path: {config.get('paths.base', 'default')}")

if __name__ == "__main__":
    main()