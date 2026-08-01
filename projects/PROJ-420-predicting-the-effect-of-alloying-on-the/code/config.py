import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

class Config:
    """Configuration management for the project."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "results"
        self.random_seed = 42
        
        # Ensure directories exist
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

def get_config() -> Config:
    """Get or create the global configuration instance."""
    return Config()

def main():
    """Test configuration loading."""
    config = get_config()
    print(f"Project Root: {config.project_root}")
    print(f"Data Raw Dir: {config.data_raw_dir}")
    print(f"Data Processed Dir: {config.data_processed_dir}")

if __name__ == "__main__":
    main()
