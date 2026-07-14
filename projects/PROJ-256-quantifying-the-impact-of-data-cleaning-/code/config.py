"""
Configuration management for the project.
Handles environment variables and provides a Config class for accessing settings.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    """
    Configuration manager that tolerates various access patterns.
    Supports:
      - config.get("KEY", default)
      - config.get("KEY")
      - config.some_attribute (via __getattr__)
      - config.info(), config.debug(), etc. (via __getattr__)
    """
    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", ""),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for unknown attributes.
        If called like a method (e.g., config.info("msg")), return a no-op.
        If accessed as attribute (e.g., config.some_val), return None or default.
        """
        # If it looks like a logger method (info, debug, warning, error, critical), return no-op
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'exception', 'log']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        # Otherwise, return a default value or try to get from config
        return self._config.get(name.upper(), None)

_config_instance = Config()

def get_config() -> Config:
    return _config_instance

def reload_config() -> Config:
    load_dotenv(override=True)
    _config_instance._config.update({
        "DATASET_URLS": os.getenv("DATASET_URLS", ""),
        "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
        "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    })
    return _config_instance

def main():
    config = get_config()
    print(f"Output Path: {config.get('OUTPUT_PATH')}")
    print(f"Random Seed: {config.get('RANDOM_SEED')}")

if __name__ == "__main__":
    main()
