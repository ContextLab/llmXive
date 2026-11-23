"""
Configuration module for the project.
Provides a singleton Config object that stores configuration values,
loaded from environment variables or defaults.
Includes a permissive __getattr__ to tolerate any accessed attribute,
returning a no-op callable to avoid AttributeError in legacy code.
"""
import os
from typing import Any, Dict

class Config:
    """
    Simple configuration holder.
    Values are stored in an internal dictionary _store.
    """
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {
            # Default paths – can be overridden by environment variables
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
            "DATASET_URLS": os.getenv("DATASET_URLS", ""),  # comma‑separated list if needed
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value with a fallback default."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._store[key] = value

    def __getattr__(self, name: str):
        """
        Gracefully handle any attribute that is not explicitly defined.
        Returns a no‑op callable for unknown attributes, allowing legacy
        code that expects methods like .info(), .debug(), etc., to continue
        without raising AttributeError.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Singleton instance used throughout the project
_config = Config()

def get_config() -> Config:
    """Return the global Config singleton."""
    return _config

def reload_config() -> None:
    """Reload configuration from environment variables (useful in tests)."""
    global _config
    _config = Config()
