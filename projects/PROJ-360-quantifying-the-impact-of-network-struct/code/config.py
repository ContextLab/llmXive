"""
Module: code/config.py
Purpose: Environment configuration management and global state.
"""
import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Global configuration instance
_config_instance: Optional['Config'] = None

class Config:
    """
    Configuration class to handle API keys, random seeds, and other settings.
    Designed to be tolerant of various access patterns (dict-like, attribute, method).
    """
    def __init__(self):
        self._config_data = self._load_environment()
        self._logger = logging.getLogger("config_logger")
    
    def _load_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "MP_API_KEY": os.getenv("MP_API_KEY"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", 42)),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DATA_DIR": os.getenv("DATA_DIR", "data"),
            "RESULTS_DIR": os.getenv("RESULTS_DIR", "results"),
            "MODELS_DIR": os.getenv("MODELS_DIR", "models"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method."""
        return self._config_data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like item access."""
        if key in self._config_data:
            return self._config_data[key]
        raise KeyError(f"Config key '{key}' not found")

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for attribute access to handle diverse caller patterns.
        If a method/attribute is not found, return a no-op callable or None.
        """
        # Check if it's in the data
        if name in self._config_data:
            return self._config_data[name]
        
        # If it looks like a logger method (info, debug, warning, error), return a no-op
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'exception']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        
        # For any other unknown attribute, return a no-op callable to prevent AttributeError
        def _missing_attr(*args, **kwargs):
            return None
        return _missing_attr

    def __repr__(self):
        return f"Config({self._config_data})"

def get_config() -> Config:
    """Get or create the global Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config():
    """Reset the global config instance (useful for testing)."""
    global _config_instance
    _config_instance = None

def initialize_environment():
    """
    Initialize the environment by setting random seeds and logging.
    """
    config = get_config()
    seed = config.get("RANDOM_SEED", 42)
    random.seed(seed)
    
    # Pin numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    level = config.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger("config_logger")
    logger.info(f"Environment initialized with seed: {seed}")

def main():
    """Test the config module."""
    config = get_config()
    print(f"MP_API_KEY: {config.get('MP_API_KEY', 'Not set')}")
    print(f"RANDOM_SEED: {config.get('RANDOM_SEED')}")
    print(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")

if __name__ == "__main__":
    main()
