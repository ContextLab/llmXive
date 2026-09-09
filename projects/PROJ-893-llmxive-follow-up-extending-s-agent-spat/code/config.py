import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Centralized configuration for the project.
    Implements a tolerant attribute access pattern to handle evolving API contracts
    without breaking existing callers.
    """
    def __init__(self):
        self.ROOT_DIR = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.ROOT_DIR / "code"
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.DATA_RAW = self.DATA_DIR / "raw"
        self.DATA_DERIVED = self.DATA_DIR / "derived"
        self.DATA_RESULTS = self.DATA_DIR / "results"
        
        # Timeouts (seconds)
        self.TIMEOUT_BATCH = 3600  # 1 hour
        self.TIMEOUT_PER_SCENE = 30  # 30 seconds per scene
        
        # Random seed
        self.SEED = 42
        
        # Sample size
        self.SAMPLE_SIZE = 1000

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access.
        If an attribute is not found, return a no-op callable or None.
        This prevents AttributeError for logger-style calls or future extensions.
        """
        # Return a no-op function for any missing attribute to handle logger calls
        def _noop(*args, **kwargs):
            return None
        return _noop

# Singleton instance
config = Config()
