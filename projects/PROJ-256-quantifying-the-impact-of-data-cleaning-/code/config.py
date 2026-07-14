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
    Provides access to environment variables and default values.
    """
    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "CLEANED_METRICS_PATH": os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"),
            "BASELINE_METRICS_PATH": os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"),
            "outcome_col": os.getenv("outcome_col", "target"),
            "group_col": os.getenv("group_col", "group"),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access for known keys."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Configuration key '{name}' not found.")

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config_instance
    load_dotenv(override=True)
    _config_instance = Config()
    return _config_instance

def main():
    """Test configuration loading."""
    cfg = get_config()
    logger.info(f"Output Path: {cfg.get('OUTPUT_PATH')}")
    logger.info(f"Random Seed: {cfg.get('RANDOM_SEED')}")

if __name__ == "__main__":
    main()
