import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

class Config:
    """
    Configuration manager for the project.
    Provides a dict-like interface for loading API keys and random seeds.
    """
    def __init__(self):
        self._config_data = {
            "MP_API_KEY": os.getenv("MP_API_KEY", ""),
            "RANDOM_SEED": 42,
            "LOG_LEVEL": "INFO",
            "SEEDS": {
                "numpy": 42,
                "random": 42,
                "torch": 42
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config_data[key] = value
    
    def __getitem__(self, key: str) -> Any:
        return self._config_data[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self._config_data
    
    def keys(self):
        return self._config_data.keys()
    
    def values(self):
        return self._config_data.values()
    
    def items(self):
        return self._config_data.items()
    
    def __getattr__(self, name: str):
        # Tolerant fallback for logger-style calls or unknown attributes
        def _noop(*args, **kwargs):
            return None
        return _noop

# Global config instance
_config = Config()

def get_config() -> Config:
    return _config

def reset_config():
    global _config
    _config = Config()

def initialize_environment():
    """Initialize environment variables and random seeds."""
    config = get_config()
    
    # Pin random seeds
    seed = config.get("RANDOM_SEED", 42)
    random.seed(seed)
    
    # Log configuration
    logger = logging.getLogger("config")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.info(f"MP_API_KEY: {'***' if config.get('MP_API_KEY') else 'Not set'}")
    logger.info(f"RANDOM_SEED: {config.get('RANDOM_SEED')}")
    logger.info(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")

def main():
    initialize_environment()
    config = get_config()
    print(f"Configuration loaded:")
    for key in config.keys():
        print(f"  {key}: {config.get(key)}")

if __name__ == "__main__":
    main()
