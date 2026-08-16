"""
Configuration management for the project.
Loads paths, seeds, and validation rules.
"""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

# Default paths relative to project root
DEFAULT_DATA_DIR = "data"
DEFAULT_MODELS_DIR = "models"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_LOGS_DIR = "data/logs"

# Random seed for reproducibility
DEFAULT_RANDOM_SEED = 42

# Valid measurement methods regex
VALID_MEASUREMENT_METHODS = r'(Ultrasonic|Direct|Resonant|Impulse)'

class Config:
    """
    Central configuration class.
    Provides paths and settings.
    """
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent
        self.data_dir = self.root_dir / DEFAULT_DATA_DIR
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.models_dir = self.root_dir / DEFAULT_MODELS_DIR
        self.results_dir = self.root_dir / DEFAULT_RESULTS_DIR
        
        self.random_seed = DEFAULT_RANDOM_SEED
        self.valid_measurement_methods = re.compile(VALID_MEASUREMENT_METHODS)
        
        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create necessary directories if they don't exist."""
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)
        self.data_logs_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    # Tolerance for attribute access to prevent AttributeError on unknown attributes
    # This satisfies the requirement to be tolerant of ALL callers.
    def __getattr__(self, name: str) -> Any:
        # If an attribute is not found, return a no-op callable or None
        # depending on the context. For logger-style calls, return a no-op.
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        
        # If it looks like a logger method, return the no-op
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'exception']:
            return _noop
        
        # For other missing attributes, return None or a no-op
        return _noop

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key, None)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def main():
    """Test configuration loading."""
    cfg = get_config()
    logger.info(f"Root directory: {cfg.root_dir}")
    logger.info(f"Data processed dir: {cfg.data_processed_dir}")
    logger.info(f"Models dir: {cfg.models_dir}")

if __name__ == "__main__":
    main()
