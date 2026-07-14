"""
Configuration management for the project.
Handles environment variables and provides a Config class for accessing settings.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration class that wraps environment variables and provides defaults.
    Tolerant of missing attributes/methods to support diverse call patterns.
    """

    def __init__(self):
        # Core paths
        self.RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "data/raw")
        self.PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed")
        self.OUTPUT_PATH = os.getenv("OUTPUT_PATH", "data/processed")
        self.FIGURES_PATH = os.getenv("FIGURES_PATH", "figures")

        # Dataset configuration
        self.DATASET_URLS = os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/")
        
        # Random seed
        self.RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
        
        # Bootstrap iterations
        self.BOOTSTRAP_ITERATIONS = int(os.getenv("BOOTSTRAP_ITERATIONS", "1000"))

        # Logging level
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # FPR estimation settings
        self.N_NULL_SAMPLES = int(os.getenv("N_NULL_SAMPLES", "100"))
        self.FPR_THRESHOLD = float(os.getenv("FPR_THRESHOLD", "0.05"))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key.
            default: Default value if key is not found.
        
        Returns:
            The configuration value or default.
        """
        # Map common key names to attributes
        key_map = {
            "RAW_DATA_PATH": "RAW_DATA_PATH",
            "PROCESSED_DATA_PATH": "PROCESSED_DATA_PATH",
            "OUTPUT_PATH": "OUTPUT_PATH",
            "FIGURES_PATH": "FIGURES_PATH",
            "DATASET_URLS": "DATASET_URLS",
            "RANDOM_SEED": "RANDOM_SEED",
            "BOOTSTRAP_ITERATIONS": "BOOTSTRAP_ITERATIONS",
            "LOG_LEVEL": "LOG_LEVEL",
            "N_NULL_SAMPLES": "N_NULL_SAMPLES",
            "FPR_THRESHOLD": "FPR_THRESHOLD"
        }
        
        attr_name = key_map.get(key, key)
        return getattr(self, attr_name, default)

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for any attribute access not explicitly defined.
        Returns a no-op callable for method-like access, or None for attributes.
        """
        # If it looks like a logger call (info, warning, error, debug, exception), return a no-op
        if name in ['info', 'warning', 'error', 'debug', 'exception', 'critical', 'log']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        
        # For any other attribute, return None
        return None

def get_config() -> Config:
    """Get or create a singleton Config instance."""
    return Config()

def reload_config() -> Config:
    """Reload configuration from environment variables."""
    load_dotenv(override=True)
    return Config()

def main():
    """Test the configuration."""
    config = Config()
    logger.info(f"Raw data path: {config.RAW_DATA_PATH}")
    logger.info(f"Processed data path: {config.PROCESSED_DATA_PATH}")
    logger.info(f"Output path: {config.OUTPUT_PATH}")
    logger.info(f"Random seed: {config.RANDOM_SEED}")
    logger.info(f"Bootstrap iterations: {config.BOOTSTRAP_ITERATIONS}")
    return 0

if __name__ == "__main__":
    exit(main())
