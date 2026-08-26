"""
Configuration management for the project.
"""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

class Config:
    """Project configuration with tolerant attribute access."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "results"
        self.specs_dir = self.project_root / "specs"
        
        # Random seed for reproducibility
        self.random_seed = 42
        
        # Valid measurement methods
        self.VALID_MEASUREMENT_METHODS = [
            r'.*Ultrasonic.*',
            r'.*Direct.*',
            r'.*Resonant.*',
            r'.*Impulse.*'
        ]
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all required directories."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_logs_dir,
            self.models_dir,
            self.results_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    # Tolerant attribute access for logger-style calls
    def __getattr__(self, name: str):
        # Handle logger-style calls (.info/.debug/.warning/.error/...)
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'log']:
            def _noop(*args: Any, **kwargs: Any) -> None:
                return None
            return _noop
        raise AttributeError(f"'Config' object has no attribute '{name}'")

_CONFIG: Optional[Config] = None

def get_config() -> Config:
    """Get or create the global config instance."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG

def main():
    """Entry point for config module."""
    config = get_config()
    print(f"Project root: {config.project_root}")
    print(f"Data directory: {config.data_dir}")
    print(f"Models directory: {config.models_dir}")
    print(f"Results directory: {config.results_dir}")

if __name__ == "__main__":
    main()
