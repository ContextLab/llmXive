import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

class Config:
    """
    Configuration manager for the project.
    Supports both attribute-style and dict-style access for compatibility.
    """
    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config_data:
            self._load_defaults()

    def _load_defaults(self):
        """Load default configuration from environment or defaults."""
        self._config_data = {
            "MP_API_KEY": os.getenv("MP_API_KEY", ""),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "MAX_RETRIES": int(os.getenv("MAX_RETRIES", "3")),
            "TIMEOUT": int(os.getenv("TIMEOUT", "30")),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        Compatible with dict.get() usage.
        """
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config_data[key] = value

    def __getitem__(self, key: str) -> Any:
        """Enable dict-style access: config['key']."""
        return self._config_data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Enable dict-style assignment: config['key'] = value."""
        self._config_data[key] = value

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for attribute access if not found in _config_data.
        Returns a no-op callable for logger-style methods (info, debug, etc.)
        to prevent AttributeError on dynamic calls.
        """
        if name in self._config_data:
            return self._config_data[name]
        
        # Return a no-op callable for unknown attributes (logger-like usage)
        def _noop(*args, **kwargs):
            return None
        return _noop

    def __contains__(self, key: str) -> bool:
        """Check if key exists in config."""
        return key in self._config_data

    def keys(self):
        """Return config keys."""
        return self._config_data.keys()

    def values(self):
        """Return config values."""
        return self._config_data.values()

    def items(self):
        """Return config items."""
        return self._config_data.items()

# Global instance
_config_instance = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config_instance
    _config_instance = Config()

def initialize_environment() -> None:
    """Initialize environment variables from config."""
    for key, value in _config_instance._config_data.items():
        if not os.getenv(key):
            os.environ[key] = str(value)

def main():
    """Main entry point for testing configuration."""
    config = get_config()
    print(f"MP_API_KEY: {config.get('MP_API_KEY', 'Not set')}")
    print(f"RANDOM_SEED: {config.get('RANDOM_SEED')}")
    print(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")

if __name__ == "__main__":
    main()
