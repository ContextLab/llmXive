import os
from pathlib import Path
from enum import Enum
from typing import Optional

class RunMode(Enum):
    REAL = "real"
    SYNTHETIC = "synthetic"
    HYBRID = "hybrid"

class Config:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"
        self.code_dir = self.base_dir / "code"
        self.tests_dir = self.base_dir / "tests"
        self.figures_dir = self.data_dir / "figures"
        self.audit_log_path = self.data_dir / "audit_log.json"
        
        # Mode selection
        self.mode = RunMode.SYNTHETIC  # Default to synthetic for safety
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        dirs = [self.data_dir, self.code_dir, self.tests_dir, self.figures_dir]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"
    
    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"
    
    @property
    def contracts_dir(self) -> Path:
        return self.data_dir / "contracts"
    
    def set_mode(self, mode: RunMode):
        self.mode = mode

# Global config instance
config = Config()
