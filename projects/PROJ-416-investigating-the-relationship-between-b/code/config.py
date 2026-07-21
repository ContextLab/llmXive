"""
Configuration module for the project.
Loads environment variables and defines paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import random
import numpy as np
from typing import Optional

# Load .env file if present
load_dotenv()

class Config:
    """
    Central configuration class.
    """
    def __init__(self):
        # Project Root
        self.ROOT_DIR = Path(__file__).resolve().parent.parent
        
        # Data Paths
        self.DATA_RAW_DIR = self.ROOT_DIR / "data" / "raw"
        self.DATA_PROCESSED_DIR = self.ROOT_DIR / "data" / "processed"
        self.DATA_METRICS_DIR = self.ROOT_DIR / "data" / "metrics"
        self.DATA_MATRICES_DIR = self.DATA_METRICS_DIR / "matrices"
        
        # Reports
        self.REPORTS_DIR = self.ROOT_DIR / "reports"
        
        # Logs
        self.LOGS_DIR = self.ROOT_DIR / "logs"
        
        # Specific Output Paths (T035 requirement)
        self.STAT_RESULTS_PATH = self.DATA_METRICS_DIR / "statistical_results.csv"
        self.SUBJECT_INFO_PATH = self.DATA_METRICS_DIR / "subject_info.json"
        self.NETWORK_METRICS_PATH = self.DATA_METRICS_DIR / "network_metrics.csv"
        self.ANALYSIS_RESULTS_PATH = self.DATA_METRICS_DIR / "analysis_results.json"
        
        # OpenNeuro Configuration
        self.OPENNEURO_ID = os.getenv("OPENNEURO_ID", "ds000030") # Default to a known dataset if needed, but T012 checks for verified
        self.MAX_SUBJECTS = int(os.getenv("MAX_SUBJECTS", "10"))
        
        # Preprocessing Thresholds
        self.MOTION_THRESHOLD_MM = float(os.getenv("MOTION_THRESHOLD_MM", "3.0"))
        self.MOTION_THRESHOLD_DEG = float(os.getenv("MOTION_THRESHOLD_DEG", "3.0"))
        
        # Statistical Parameters
        self.ALPHA = float(os.getenv("ALPHA", "0.05"))
        self.POWER_TARGET = float(os.getenv("POWER_TARGET", "0.8"))
        self.EFFECT_SIZE_F2 = float(os.getenv("EFFECT_SIZE_F2", "0.15"))
        
        # Random Seed
        self.RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
        random.seed(self.RANDOM_SEED)
        np.random.seed(self.RANDOM_SEED)

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.DATA_RAW_DIR,
            self.DATA_PROCESSED_DIR,
            self.DATA_METRICS_DIR,
            self.DATA_MATRICES_DIR,
            self.REPORTS_DIR,
            self.LOGS_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

# Singleton instance
config = Config()
