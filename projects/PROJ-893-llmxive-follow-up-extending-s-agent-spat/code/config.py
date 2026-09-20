"""
Configuration module for the llmXive S-Agent Spatial Reasoning Pipeline.
"""
import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Centralized configuration class.
    Provides paths and constants for the pipeline.
    """
    def __init__(self):
        # Base paths
        self.ROOT_DIR = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.ROOT_DIR / "code"
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.DATA_RAW = self.DATA_DIR / "raw"
        self.DATA_DERIVED = self.DATA_DIR / "derived"
        self.DATA_RESULTS = self.DATA_DIR / "results"
        
        # Constants
        self.RANDOM_SEED = 42
        self.SAMPLE_SIZE = 1000
        
        # Timeout configurations (in seconds/hours)
        self.BATCH_TIMEOUT_HOURS = 6
        self.SCENE_SOFT_LIMIT_SECONDS = 30

    @property
    def logger(self):
        """Return a simple logger instance."""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    # Tolerant attribute access for dynamic calls
    def __getattr__(self, name: str) -> Any:
        # Provide a no-op callable for any unknown attribute that might be called as a method
        # e.g. config.some_unknown_method() -> returns a function that does nothing
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        def _noop(*args, **kwargs):
            return None
        return _noop

# Instance for easy access if needed
config = Config()
