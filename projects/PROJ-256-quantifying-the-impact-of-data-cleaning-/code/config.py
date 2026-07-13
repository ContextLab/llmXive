"""
Configuration management for the project.

Provides a Config class that supports both attribute-like access (Config.KEY)
and dictionary-like access (Config.get('KEY')), tolerating unknown keys.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration container.
    Supports attribute access (config.RANDOM_SEED) and dict-like access (config.get('RANDOM_SEED')).
    Unknown attributes/methods return a no-op or default value to prevent crashes.
    """
    
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        self._data = {}
        
        # Default configuration
        defaults = {
            "DATASET_URLS": os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", 42)),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", 1000)),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }
        
        self._data.update(defaults)
        if overrides:
            self._data.update(overrides)
    
    def __getattr__(self, name: str) -> Any:
        """Handle attribute-like access (e.g., config.RANDOM_SEED)."""
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._data:
            return self._data[name]
        # Fallback for unknown attributes: return None or a default
        # For logger-like calls, we return a no-op function
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'get', 'set']:
            return self._no_op
        return None
    
    def __getitem__(self, key: str) -> Any:
        """Handle dictionary-like access (e.g., config['RANDOM_SEED'])."""
        return self._data.get(key)
    
    def _no_op(self, *args, **kwargs) -> Any:
        """No-operation function for unknown method calls."""
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get method."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._data[key] = value
    
    def items(self):
        """Return items for iteration."""
        return self._data.items()
    
    def keys(self):
        """Return keys."""
        return self._data.keys()
    
    def values(self):
        """Return values."""
        return self._data.values()

def get_config(overrides: Optional[Dict[str, Any]] = None) -> Config:
    """Factory function to get a Config instance."""
    return Config(overrides)

def reload_config() -> Config:
    """Reload configuration from environment variables."""
    load_dotenv(override=True)
    return get_config()

def main():
    """CLI entry point for config module (testing)."""
    config = get_config()
    print(f"Random Seed: {config.RANDOM_SEED}")
    print(f"Output Path: {config.get('OUTPUT_PATH')}")
    print(f"Unknown Key: {config.get('NON_EXISTENT_KEY', 'default')}")
    config.info("This is a test log message")
    print("Config loaded successfully.")

if __name__ == "__main__":
    main()
