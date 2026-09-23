"""
Configuration management for the llmXive project.
"""
import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Centralized configuration class.
    Handles paths, seeds, and constants.
    """
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.PROJECT_ROOT / "code"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.DATA_RAW = self.DATA_DIR / "raw"
        self.DATA_DERIVED = self.DATA_DIR / "derived"
        self.DATA_RESULTS = self.DATA_DIR / "results"
        self.SPECS_DIR = self.PROJECT_ROOT / "specs" / "001-symbolic-spatial-reasoning"
        
        # Constants
        self.RANDOM_SEED = 42
        self.SAMPLE_SIZE = 1000
        self.BATCH_TIMEOUT_HOURS = 6
        self.SCENE_SOFT_LIMIT_SECONDS = 300

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.DATA_RAW,
            self.DATA_DERIVED,
            self.DATA_RESULTS,
            self.CODE_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # Logger-like methods for tolerance
    def info(self, msg: str):
        print(f"INFO: {msg}")

    def error(self, msg: str):
        print(f"ERROR: {msg}")

    def warning(self, msg: str):
        print(f"WARNING: {msg}")

    def debug(self, msg: str):
        print(f"DEBUG: {msg}")

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for any undefined attribute to prevent AttributeError
        in scripts that might call dynamic methods on Config.
        Returns a no-op callable or None.
        """
        def _no_op(*args, **kwargs):
            return None
        return _no_op

# Global instance
config = Config()
