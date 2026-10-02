import os
from pathlib import Path
from typing import Any, Optional

class Config:
    """
    Global configuration for the llmXive project.
    Handles paths, seeds, and logging-like attributes.
    """
    # Base paths
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_RAW = DATA_DIR / "raw"
    DATA_DERIVED = DATA_DIR / "derived"
    DATA_RESULTS = DATA_DIR / "results"
    CODE_DIR = PROJECT_ROOT / "code"
    SPECS_DIR = PROJECT_ROOT / "specs"
    
    # Derived paths (convenience)
    DERIVED_PATH = DATA_DERIVED
    RESULTS_PATH = DATA_RESULTS
    RAW_PATH = DATA_RAW

    # Constants
    SAMPLE_SIZE = 1000
    RANDOM_SEED = 42
    BATCH_TIMEOUT_HOURS = 6
    SCENE_SOFT_LIMIT_SECONDS = 300
    
    # Logging-like attributes (to satisfy flexible callers)
    def info(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def critical(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass

    # Fallback for any other attribute access to prevent AttributeError
    def __getattr__(self, name: str) -> Any:
        # Return a no-op callable for any unknown attribute access
        # This allows scripts to call Config.some_unknown_method(...) without crashing
        def _noop(*args, **kwargs):
            return None
        return _noop

# Singleton instance for convenience
config = Config()
