"""Configuration management for the project."""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

class Config:
    """Configuration class for project paths and settings."""
    
    def __init__(self):
        # Base paths
        self.root_dir = Path(__file__).parent.parent
        self.code_dir = self.root_dir / "code"
        self.data_dir = self.root_dir / "data"
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.models_dir = self.root_dir / "models"
        self.results_dir = self.root_dir / "results"
        self.specs_dir = self.root_dir / "specs"
        self.docs_dir = self.root_dir / "docs"
        self.tests_dir = self.root_dir / "tests"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Settings
        self.random_seed = 42
        self.mp_api_key = os.getenv("MP_API_KEY", "")
        
        # Valid measurement methods regex
        self.VALID_MEASUREMENT_METHODS = r'(Ultrasonic|Direct|Resonant|Impulse)'
        
        # Element list for Al alloys
        self.major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
        self.alloy_base = 'Al'
        
        # Thresholds
        self.major_element_sum_threshold = 0.95
        self.vif_threshold = 5.0
        self.mae_threshold = 0.05
        
        # Logger
        self.logger = get_logger("config")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_logs_dir,
            self.models_dir,
            self.results_dir,
            self.specs_dir,
            self.docs_dir,
            self.tests_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    # Backward compatibility aliases
    @property
    def data_processed(self):
        """Alias for data_processed_dir for backward compatibility."""
        return self.data_processed_dir
    
    def __getattr__(self, name: str):
        """Tolerant attribute access for unknown logger-style calls."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_CONFIG: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG

def main():
    """Main entry point for config (testing)."""
    config = get_config()
    print(f"Root directory: {config.root_dir}")
    print(f"Data directory: {config.data_dir}")
    print(f"Models directory: {config.models_dir}")
    print(f"Results directory: {config.results_dir}")

if __name__ == "__main__":
    main()
