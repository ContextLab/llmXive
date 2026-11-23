import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Paths
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.DATA_RAW = self.PROJECT_ROOT / "data" / "raw"
        self.DATA_PROCESSED = self.PROJECT_ROOT / "data" / "processed"
        self.DATA_METRICS = self.PROJECT_ROOT / "data" / "metrics"
        self.REPORTS_DIR = self.PROJECT_ROOT / "reports"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Ensure directories exist
        self.DATA_RAW.mkdir(parents=True, exist_ok=True)
        self.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        self.DATA_METRICS.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.VERIFIED_SOURCES_PATH = str(self.DATA_METRICS / "verified_sources.json")
        self.NETWORK_METRICS_PATH = str(self.DATA_METRICS / "network_metrics.csv")
        self.STATISTICAL_RESULTS_PATH = str(self.DATA_METRICS / "statistical_results.csv")
        self.POWER_ANALYSIS_PATH = str(self.DATA_METRICS / "power_analysis.json")
        self.REPORTS_RESULTS_PATH = str(self.REPORTS_DIR / "results.md")
        
        # Configuration
        self.OPENNEURO_ID = os.getenv("OPENNEURO_ID", "ds000000")
        self.SEED = int(os.getenv("RANDOM_SEED", "42"))
        self.MAX_SUBJECTS = int(os.getenv("MAX_SUBJECTS", "20"))
        self.ATLAS = os.getenv("ATLAS", "Schaefer-100")
        
        # Power analysis defaults
        self.POWER_EFFECT_SIZE = float(os.getenv("POWER_EFFECT_SIZE", "0.15"))
        self.POWER_ALPHA = float(os.getenv("POWER_ALPHA", "0.05"))
        self.POWER_TARGET = float(os.getenv("POWER_TARGET", "0.80"))