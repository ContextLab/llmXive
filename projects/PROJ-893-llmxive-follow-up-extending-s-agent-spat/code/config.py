import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Central configuration for the project.
    Handles paths, seeds, and tolerant attribute access for logging-like usage.
    """
    def __init__(self):
        self.ROOT_DIR = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.ROOT_DIR / "code"
        self.DATA_RAW = self.ROOT_DIR / "data" / "raw"
        self.DATA_DERIVED = self.ROOT_DIR / "data" / "derived"
        self.DATA_RESULTS = self.ROOT_DIR / "data" / "results"
        self.SPECS_DIR = self.ROOT_DIR / "specs" / "001-symbolic-spatial-reasoning"
        
        # Aliases for backward compatibility and specific caller needs
        self.DATA_DIR = self.DATA_RAW  # Often used for input data
        self.DERIVED_PATH = self.DATA_DERIVED
        
        # Constants
        self.RANDOM_SEED = 42
        self.SAMPLE_SIZE = 1000
        self.TIMEOUT_GLOBAL = 21600  # 6 hours
        self.TIMEOUT_PER_SCENE = 300  # 5 minutes

    # Tolerant __getattr__ to handle dynamic logging calls or undefined attributes gracefully
    def __getattr__(self, name: str) -> Any:
        # If an attribute is not found (e.g., a logger method call like .info()), return a no-op
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

# Singleton instance
CONFIG = Config()
