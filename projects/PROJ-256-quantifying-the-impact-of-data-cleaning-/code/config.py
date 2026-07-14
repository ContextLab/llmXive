import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class for the project.
    Provides access to environment variables and default values.
    """
    
    # Default values
    _defaults = {
        "DATASET_URLS": "https://archive.ics.uci.edu/ml/machine-learning-databases/",
        "OUTPUT_PATH": "data/processed",
        "RANDOM_SEED": 42,
        "BOOTSTRAP_ITERATIONS": 1000,
        "RAW_DATA_PATH": "data/raw",
        "PROCESSED_DATA_PATH": "data/processed",
        "FIGURES_PATH": "figures",
        "LOG_LEVEL": "INFO",
        "outcome_col": None,
        "group_col": None
    }
    
    def __init__(self):
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and defaults."""
        for key, default_value in self._defaults.items():
            env_value = os.getenv(key)
            if env_value is not None:
                # Try to convert to appropriate type
                if isinstance(default_value, int):
                    try:
                        self._config[key] = int(env_value)
                    except ValueError:
                        self._config[key] = default_value
                elif isinstance(default_value, bool):
                    self._config[key] = env_value.lower() in ('true', '1', 'yes')
                else:
                    self._config[key] = env_value
            else:
                self._config[key] = default_value
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return key in self._config
    
    def keys(self):
        """Return all keys."""
        return self._config.keys()
    
    def values(self):
        """Return all values."""
        return self._config.values()
    
    def items(self):
        """Return all items."""
        return self._config.items()
    
    # Logger-style methods for compatibility
    def info(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass
    
    def debug(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass
    
    def warning(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass
    
    def error(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass
    
    def critical(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass
    
    def exception(self, *args, **kwargs):
        """No-op for logger-style calls."""
        pass

# Global config instance
_config_instance = None

def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """
    Reload the global configuration instance.
    
    Returns:
        New Config instance
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance

def main():
    """
    Main entry point for config module.
    """
    logger = logging.getLogger(__name__)
    logger.info("Config module loaded")
    config = get_config()
    logger.info(f"Config keys: {list(config.keys())}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
