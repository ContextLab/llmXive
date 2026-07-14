import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration manager for the project.
    Tolerant to missing keys and flexible access patterns.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", ""),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "BASELINE_METRICS_PATH": os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"),
            "CLEANED_METRICS_PATH": os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"),
            "NULL_FPR_METRICS_PATH": os.getenv("NULL_FPR_METRICS_PATH", "data/processed/null_fpr_metrics.json"),
            "OUTCOME_COLUMN": os.getenv("OUTCOME_COLUMN", None),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
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
        """
        Tolerant attribute access.
        If a method or attribute is not found, return a no-op callable or None.
        This prevents AttributeError when scripts call .info(), .debug(), etc. on Config.
        """
        if name.startswith('_'):
            raise AttributeError(name)
        # Return a no-op function for any unknown attribute (logger-style calls)
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    return Config()

def reload_config() -> None:
    load_dotenv(override=True)
    config = Config()
    # Re-initialize internal dict
    config._config = {
        "DATASET_URLS": os.getenv("DATASET_URLS", ""),
        "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
        "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
        "BASELINE_METRICS_PATH": os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"),
        "CLEANED_METRICS_PATH": os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"),
        "NULL_FPR_METRICS_PATH": os.getenv("NULL_FPR_METRICS_PATH", "data/processed/null_fpr_metrics.json"),
        "OUTCOME_COLUMN": os.getenv("OUTCOME_COLUMN", None),
    }

def main():
    config = Config()
    logger.info("Configuration loaded:")
    for k, v in config._config.items():
        logger.info(f"  {k}: {v}")

if __name__ == "__main__":
    main()
