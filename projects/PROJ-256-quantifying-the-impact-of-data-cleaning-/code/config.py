import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager for the project.
    Tolerant of missing attributes by returning default values or None.
    """
    
    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "OUTCOME_COLUMN": os.getenv("OUTCOME_COLUMN", "outcome"),
            "PREDICTOR_COLUMN": os.getenv("PREDICTOR_COLUMN", "predictor"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO")
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        """
        return self._config.get(key, default)
    
    def __getattr__(self, name: str) -> Any:
        """
        Fallback for attribute access (e.g., config.some_var).
        Returns None if not found.
        """
        if name.startswith('_'):
            raise AttributeError(name)
        return self._config.get(name, None)
    
    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access: config['key']
        """
        return self._config.get(key, None)
    
    def __contains__(self, key: str) -> bool:
        return key in self._config

# Global instance
_config_instance = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    global _config_instance
    _config_instance = Config()
    return _config_instance

def main():
    """
    Test config loading.
    """
    cfg = get_config()
    print(f"Output Path: {cfg.get('OUTPUT_PATH')}")
    print(f"Random Seed: {cfg.get('RANDOM_SEED')}")
    # Test tolerant access
    print(f"Unknown Key: {cfg.get('UNKNOWN_KEY', 'default')}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
