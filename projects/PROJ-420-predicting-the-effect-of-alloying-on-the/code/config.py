"""
Configuration management for the project.
"""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

class Config:
    """
    Configuration container.
    Tolerant of unknown attribute accesses via __getattr__.
    """
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.data_dir = self.root_dir / "data"
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.models_dir = self.root_dir / "models"
        self.results_dir = self.root_dir / "results"
        
        # Ensure directories exist
        for d in [self.data_raw_dir, self.data_processed_dir, self.data_logs_dir, self.models_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Validation regex
        self.VALID_MEASUREMENT_METHODS = r'(Ultrasonic|Direct|Resonant|Impulse)'
        
        # Aliases for compatibility
        self.data_processed = self.data_processed_dir
        self.data_logs = self.data_logs_dir

    # Tolerant attribute access
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_CONFIG: Optional[Config] = None

def get_config() -> Config:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG

def main():
    config = get_config()
    logger = get_logger()
    logger.info("Config loaded")
    print(json.dumps({
        "data_processed": str(config.data_processed),
        "data_logs": str(config.data_logs)
    }, indent=2))

if __name__ == "__main__":
    main()