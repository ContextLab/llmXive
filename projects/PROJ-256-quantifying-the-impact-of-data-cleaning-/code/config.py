import os
from typing import Any, Dict, Optional

class Config:
    """
    Configuration management class.
    Acts as a dictionary-like object for getting config values.
    """
    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        self._config[key] = value

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access for logger-like calls or missing keys.
        Returns a no-op function for unknown methods/attributes.
        """
        if name in self._config:
            return self._config[name]
        # Return a no-op callable for any unknown attribute
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    return Config()

def reload_config() -> Config:
    return get_config()

config = get_config()
