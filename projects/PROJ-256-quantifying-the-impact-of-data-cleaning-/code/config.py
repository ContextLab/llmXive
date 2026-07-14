import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the project."""
    
    def __init__(self):
        load_dotenv()
        self._config = {
            'DATASET_URLS': os.getenv('DATASET_URLS', 'https://archive.ics.uci.edu/ml/machine-learning-databases/'),
            'OUTPUT_PATH': os.getenv('OUTPUT_PATH', 'data/processed'),
            'RAW_DATA_PATH': os.getenv('RAW_DATA_PATH', 'data/raw'),
            'PROCESSED_DATA_PATH': os.getenv('PROCESSED_DATA_PATH', 'data/processed'),
            'RANDOM_SEED': int(os.getenv('RANDOM_SEED', '42')),
            'BOOTSTRAP_ITERATIONS': int(os.getenv('BOOTSTRAP_ITERATIONS', '1000')),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in config."""
        return key in self._config
    
    def keys(self) -> List[str]:
        """Return all keys."""
        return list(self._config.keys())
    
    def values(self) -> List[Any]:
        """Return all values."""
        return list(self._config.values())
    
    def items(self) -> List[tuple]:
        """Return all items."""
        return list(self._config.items())
    
    # Tolerant fallback for any attribute access
    def __getattr__(self, name: str) -> Any:
        """Handle unknown attributes gracefully."""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        # Return a no-op callable for logger-style calls
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()

def reload_config():
    """Reload configuration from environment variables."""
    load_dotenv(override=True)
    return get_config()

def main():
    """Main entry point for config module."""
    config = get_config()
    logger.info(f"Output path: {config.get('OUTPUT_PATH')}")
    logger.info(f"Random seed: {config.get('RANDOM_SEED')}")

if __name__ == "__main__":
    main()
