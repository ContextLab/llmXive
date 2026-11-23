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

    Paths are defined BOTH at class level (so `Config.DATA_DERIVED`,
    `Config.DERIVED_PATH`, `Config.DATA_DIR`, ... work without
    instantiation) and at instance level (unchanged behavior for
    existing callers that do `Config()`).
    """

    # Class-level path attributes (additive; instance copies below)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CODE_DIR = PROJECT_ROOT / "code"
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_RAW = DATA_DIR / "raw"
    DATA_DERIVED = DATA_DIR / "derived"
    DATA_RESULTS = DATA_DIR / "results"
    DERIVED_PATH = DATA_DERIVED
    SPECS_DIR = PROJECT_ROOT / "specs"

    def __init__(self):
        self.PROJECT_ROOT = Config.PROJECT_ROOT
        self.CODE_DIR = Config.CODE_DIR
        self.DATA_DIR = Config.DATA_DIR
        self.DATA_RAW = Config.DATA_RAW
        self.DATA_DERIVED = Config.DATA_DERIVED
        self.DATA_RESULTS = Config.DATA_RESULTS
        self.DERIVED_PATH = Config.DERIVED_PATH
        self.SPECS_DIR = Config.SPECS_DIR

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
