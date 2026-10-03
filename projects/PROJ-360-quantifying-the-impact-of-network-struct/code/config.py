import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the project."""
    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._load_config()

    def _load_config(self):
        """Load configuration from environment variables."""
        self._config_data = {
            "MP_API_KEY": os.getenv("MP_API_KEY", ""),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DATA_DIR": os.getenv("DATA_DIR", "data"),
            "CODE_DIR": os.getenv("CODE_DIR", "code"),
            "RESULTS_DIR": os.getenv("RESULTS_DIR", "results"),
            "MODELS_DIR": os.getenv("MODELS_DIR", "models")
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config_data[key] = value

    def get_random_seed(self) -> int:
        """Get the random seed."""
        return self._config_data.get("RANDOM_SEED", 42)

    def get_api_key(self) -> str:
        """Get the Materials Project API key."""
        return self._config_data.get("MP_API_KEY", "")

    # Tolerant logger-style fallback for dynamic calls
    def __getattr__(self, name: str):
        # Any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    """Get the singleton Config instance."""
    return Config()

def reset_config() -> None:
    """Reset the configuration (useful for testing)."""
    Config._instance = None
    Config._config_data = {}

def initialize_environment() -> None:
    """Initialize environment based on config."""
    config = get_config()
    seed = config.get_random_seed()
    random.seed(seed)
    logging.info(f"Initialized environment with seed {seed}")

def main():
    """Main entry point for config testing."""
    config = get_config()
    print(f"MP_API_KEY: {config.get('MP_API_KEY', 'Not set')}")
    print(f"RANDOM_SEED: {config.get('RANDOM_SEED')}")
    print(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")

if __name__ == "__main__":
    main()
