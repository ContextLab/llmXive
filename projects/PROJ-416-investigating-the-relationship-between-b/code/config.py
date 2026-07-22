import os
from pathlib import Path
# Removed dotenv import to avoid dependency error if not installed,
# relying on environment variables directly as per standard CI practices.
# If .env support is strictly required, python-dotenv must be in requirements.txt.
# For now, we assume env vars are set by the runner.
import random
import numpy as np
from typing import Optional

class Config:
    """
    Central configuration management for the project.
    Loads settings from environment variables or defaults.
    """
    
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.CODE_DIR = self.PROJECT_ROOT / "code"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.RAW_DATA_DIR = self.DATA_DIR / "raw"
        self.PROCESSED_DATA_DIR = self.DATA_DIR / "processed"
        self.METRICS_DIR = self.DATA_DIR / "metrics"
        self.REPORTS_DIR = self.PROJECT_ROOT / "reports"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Ensure directories exist
        for d in [self.DATA_DIR, self.RAW_DATA_DIR, self.PROCESSED_DATA_DIR, 
                  self.METRICS_DIR, self.REPORTS_DIR, self.LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        # OpenNeuro Configuration
        # T041: This ID MUST match the one in data/verified_sources.json
        self.OPENNEURO_ID = os.getenv("OPENNEURO_ID", "ds004563")
        self.OPENNEURO_VERSION = os.getenv("OPENNEURO_VERSION", "1.0.0")
        
        # Processing Parameters
        self.MOTION_THRESHOLD_MM = float(os.getenv("MOTION_THRESHOLD_MM", 3.0))
        self.MOTION_THRESHOLD_DEG = float(os.getenv("MOTION_THRESHOLD_DEG", 3.0))
        self.SUBSET_SIZE = int(os.getenv("SUBSET_SIZE", 10))
        
        # Random Seeds for reproducibility
        self.RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))
        random.seed(self.RANDOM_SEED)
        np.random.seed(self.RANDOM_SEED)
