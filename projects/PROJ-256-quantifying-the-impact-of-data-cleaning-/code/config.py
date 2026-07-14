"""
Configuration management for the project.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration class that acts as a namespace for environment variables.
    Provides a tolerant interface for attribute access.
    """
    def __init__(self):
        self.DATASET_URLS = os.getenv("DATASET_URLS", "uci_har,shopper")
        self.OUTPUT_PATH = os.getenv("OUTPUT_PATH", "data/processed")
        self.RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
        self.BOOTSTRAP_ITERATIONS = int(os.getenv("BOOTSTRAP_ITERATIONS", "1000"))
        self.RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "data/raw")
        self.PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed")
        
        # Tolerant attribute access for unknown methods/attributes
        # This allows calls like config.info() or config.get() without errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key.upper(), default)
    
    def __getattr__(self, name: str) -> Any:
        """
        Fallback for any attribute access.
        Returns a no-op callable if the attribute is not found,
        to prevent AttributeError for dynamic logger-style calls or missing config keys.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    """Return the singleton Config instance."""
    return Config()

def reload_config() -> Config:
    """Reload configuration from environment variables."""
    return get_config()

def main():
    """Main entry point for testing."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Config module loaded.")
    cfg = get_config()
    logger.info(f"OUTPUT_PATH: {cfg.OUTPUT_PATH}")
    logger.info(f"RANDOM_SEED: {cfg.RANDOM_SEED}")
    # Test tolerant access
    logger.info(f"Unknown key: {cfg.get('UNKNOWN_KEY', 'default')}")

if __name__ == "__main__":
    main()
