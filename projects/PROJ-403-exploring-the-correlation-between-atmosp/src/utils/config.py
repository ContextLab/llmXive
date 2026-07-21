import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

DEFAULT_AR_THRESHOLD = 10.0 # kg m^-1 s^-1

@dataclass
class Config:
    """Configuration container for the project."""
    data_dir: str = "data"
    processed_dir: str = "data/processed"
    figures_dir: str = "figures"
    logs_dir: str = "logs"
    report_dir: str = "report"
    artifacts_dir: str = "artifacts"
    
    # AR Detection
    ar_threshold: float = DEFAULT_AR_THRESHOLD
    
    # Regional Domain
    lat_min: float = 20.0
    lat_max: float = 60.0
    lon_min: float = 100.0
    lon_max: float = 300.0 # 60W in 0-360

    def __post_init__(self):
        """Initialize directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.processed_dir,
            self.figures_dir,
            self.logs_dir,
            self.report_dir,
            self.artifacts_dir
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the singleton Config instance.
    Reads environment variables if set.
    """
    global _config_instance
    if _config_instance is None:
        config = Config()
        
        # Override with environment variables if present
        if os.getenv("DATA_DIR"):
            config.data_dir = os.getenv("DATA_DIR")
        if os.getenv("PROCESSED_DIR"):
            config.processed_dir = os.getenv("PROCESSED_DIR")
        if os.getenv("FIGURES_DIR"):
            config.figures_dir = os.getenv("FIGURES_DIR")
        if os.getenv("LOGS_DIR"):
            config.logs_dir = os.getenv("LOGS_DIR")
        if os.getenv("REPORT_DIR"):
            config.report_dir = os.getenv("REPORT_DIR")
        if os.getenv("ARTIFACTS_DIR"):
            config.artifacts_dir = os.getenv("ARTIFACTS_DIR")
        if os.getenv("AR_THRESHOLD"):
            config.ar_threshold = float(os.getenv("AR_THRESHOLD"))
        
        _config_instance = config
    return _config_instance
