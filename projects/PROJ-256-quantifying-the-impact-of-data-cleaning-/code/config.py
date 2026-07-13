"""
Configuration management for the project.
Handles environment variables and provides a Config class.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration class that acts as a dictionary-like accessor for environment variables.
    Tolerant of missing keys and provides default values.
    """
    _defaults = {
        "DATASET_URLS": "",
        "OUTPUT_PATH": "data/processed",
        "RANDOM_SEED": 42,
        "BOOTSTRAP_ITERATIONS": 1000,
        "RAW_DATA_PATH": "data/raw",
        "PROCESSED_DATA_PATH": "data/processed",
        "LOG_LEVEL": "INFO"
    }

    def __init__(self):
        self._config = {**self._defaults}
        for key in self._defaults:
            val = os.getenv(key)
            if val is not None:
                # Try to convert to int if possible
                try:
                    self._config[key] = int(val)
                except ValueError:
                    self._config[key] = val

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default if default is not None else self._defaults.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    # Tolerant logger-style methods for dynamic access
    def __getattr__(self, name: str) -> Any:
        # If an attribute is accessed that doesn't exist, return a no-op callable
        # This handles cases like config.info(), config.debug(), etc.
        def _noop(*args, **kwargs):
            return None
        return _noop

# Global instance
_config_instance = Config()

def get_config() -> Config:
    return _config_instance

def reload_config() -> None:
    global _config_instance
    _config_instance = Config()

def main():
    """Test the config."""
    print(f"Random Seed: {_config_instance.get('RANDOM_SEED')}")
    print(f"Output Path: {_config_instance.get('OUTPUT_PATH')}")

if __name__ == "__main__":
    main()
