import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Project configuration loaded from environment variables."""
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
    DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
    DATA_METRICS: Path = PROJECT_ROOT / "data" / "metrics"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    
    # Data Sources
    OPENNEURO_ID: str = os.getenv("OPENNEURO_ID", "ds000030")
    VERIFIED_SOURCES_PATH: Path = PROJECT_ROOT / "data" / "verified_sources.json"
    
    # Processing Parameters
    MOTION_THRESHOLD_MM: float = float(os.getenv("MOTION_THRESHOLD_MM", "3.0"))
    MOTION_THRESHOLD_DEG: float = float(os.getenv("MOTION_THRESHOLD_DEG", "3.0"))
    N_SUBSETS: int = int(os.getenv("N_SUBSETS", "10"))
    
    # Analysis Parameters
    ATLAS_NAME: str = os.getenv("ATLAS_NAME", "aal")
    ALPHA: float = float(os.getenv("ALPHA", "0.05"))
    POWER_TARGET: float = float(os.getenv("POWER_TARGET", "0.8"))
    EFFECT_SIZE: float = float(os.getenv("EFFECT_SIZE", "0.15"))
    
    # Seeds
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "42"))
    
    @classmethod
    def ensure_directories(cls):
        """Create all required directories if they don't exist."""
        for path in [cls.DATA_RAW, cls.DATA_PROCESSED, cls.DATA_METRICS, cls.LOGS_DIR, cls.REPORTS_DIR]:
            path.mkdir(parents=True, exist_ok=True)