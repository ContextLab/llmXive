"""
Configuration management module.

Provides a Config class that wraps environment variables and provides
a tolerant interface for accessing configuration values.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager.
    
    Acts as a tolerant dictionary-like object for accessing environment variables.
    Implements __getattr__ to handle dynamic attribute access (e.g., config.get(...))
    and method calls (e.g., config.info(...)) gracefully.
    """
    
    def __init__(self):
        # Cache of loaded values
        self._cache: Dict[str, Any] = {}
        # Load defaults if not in env
        self.defaults = {
            "RAW_DATA_PATH": "data/raw",
            "PROCESSED_DATA_PATH": "data/processed",
            "FIGURES_PATH": "figures",
            "RANDOM_SEED": "42",
            "BOOTSTRAP_ITERATIONS": "1000",
            "LOG_LEVEL": "INFO",
            "DATASET_URLS": "https://archive.ics.uci.edu/ml/machine-learning-databases/"
        }
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Priority:
        1. Environment variable
        2. Internal cache
        3. Default value from self.defaults
        4. Provided default argument
        """
        if key in self._cache:
            return self._cache[key]
        
        val = os.getenv(key)
        if val is not None:
            self._cache[key] = val
            return val
        
        if key in self.defaults:
            self._cache[key] = self.defaults[key]
            return self.defaults[key]
        
        if default is not None:
            self._cache[key] = default
            return default
        
        return None

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access.
        
        Allows calls like config.info(), config.warning(), etc., to be no-ops.
        Allows access like config.RAW_DATA_PATH to be mapped to get().
        """
        # Handle logger-style method calls (info, warning, error, debug)
        if name in ['info', 'warning', 'error', 'debug', 'critical', 'exception']:
            def _noop_logger(*args, **kwargs):
                # Optionally log if logger is configured, otherwise ignore
                # We use the module-level logger to avoid infinite recursion
                if hasattr(logging, name):
                    func = getattr(logger, name)
                    func(*args, **kwargs)
                return None
            return _noop_logger
        
        # Handle standard config access (e.g., config.RAW_DATA_PATH)
        # If it looks like a config key, try to get it
        if name.isupper() or name in self.defaults:
            return self.get(name)
        
        # Default fallback for unknown attributes
        return None

    def reload(self):
        """Reload configuration from environment variables."""
        self._cache.clear()
        load_dotenv(override=True)

def get_config() -> Config:
    """Return a singleton Config instance."""
    # Simple singleton pattern
    if not hasattr(get_config, "_instance"):
        get_config._instance = Config()
    return get_config._instance

def reload_config():
    """Reload the singleton config."""
    cfg = get_config()
    cfg.reload()

def main():
    """Test configuration."""
    cfg = get_config()
    print(f"RAW_DATA_PATH: {cfg.get('RAW_DATA_PATH')}")
    print(f"PROCESSED_DATA_PATH: {cfg.get('PROCESSED_DATA_PATH')}")
    print(f"Unknown Key (should be None): {cfg.get('NONEXISTENT_KEY')}")
    print(f"Unknown Key with default: {cfg.get('NONEXISTENT_KEY', 'default_val')}")
    
    # Test tolerant attribute access
    cfg.info("This is an info message via config")
    cfg.warning("This is a warning message via config")

if __name__ == "__main__":
    main()