"""
Configuration module for the llmXive project.
Handles paths, seeds, and global settings.
"""
import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Central configuration class.
    Provides access to project paths and global settings.
    Includes a tolerant __getattr__ for logging-style calls.
    """
    
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.PROJECT_ROOT / "code"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.DATA_RAW = self.DATA_DIR / "raw"
        self.DATA_DERIVED = self.DATA_DIR / "derived"
        self.DATA_RESULTS = self.DATA_DIR / "results"
        self.SPECS_DIR = self.PROJECT_ROOT / "specs"
        
        # Constants
        self.RANDOM_SEED = 42
        self.SAMPLE_SIZE = 1000
        
        # Solver settings
        self.BATCH_TIMEOUT_HOURS = 6
        self.SCENE_SOFT_LIMIT_SECONDS = 30.0
        self.WORKERS = 2

    # Tolerant attribute access for logger-style calls
    def __getattr__(self, name: str) -> Any:
        # If an attribute is not found, return a no-op callable
        # This prevents AttributeError on calls like config.info(), config.error(), etc.
        def _noop(*args, **kwargs):
            return None
        return _noop

    def get_path(self, key: str) -> Optional[Path]:
        """Retrieve a path attribute by name."""
        val = getattr(self, key, None)
        if isinstance(val, Path):
            return val
        return None