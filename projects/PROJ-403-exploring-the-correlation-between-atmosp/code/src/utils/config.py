import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration management for the project."""
    data_root: str = "data"
    processed_dir: str = "data/processed"
    figures_dir: str = "figures"
    logs_dir: str = "logs"
    report_dir: str = "report"
    artifacts_dir: str = "artifacts"
    
    # Regional Domain (20°N-60°N, 100°E-60°W)
    # CDS Area format: [North, West, South, East]
    # North: 60, West: -60 (60°W), South: 20, East: 100 (100°E)
    # Note: 100°E is 100, 60°W is -60.
    # CDS expects [North, West, South, East]
    region_area: list = field(default_factory=lambda: [60.0, -60.0, 20.0, 100.0])
    
    # Years
    start_year: int = 1979
    end_year: int = 2023
    
    # Thresholds
    ar_threshold: float = 100.0  # kg m-1 s-1 (example default)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            data_root=os.getenv("DATA_ROOT", "data"),
            processed_dir=os.getenv("PROCESSED_DIR", "data/processed"),
            figures_dir=os.getenv("FIGURES_DIR", "figures"),
            logs_dir=os.getenv("LOGS_DIR", "logs"),
            report_dir=os.getenv("REPORT_DIR", "report"),
            artifacts_dir=os.getenv("ARTIFACTS_DIR", "artifacts"),
            region_area=[
                float(os.getenv("REGION_NORTH", "60.0")),
                float(os.getenv("REGION_WEST", "-60.0")),
                float(os.getenv("REGION_SOUTH", "20.0")),
                float(os.getenv("REGION_EAST", "100.0")),
            ],
            start_year=int(os.getenv("START_YEAR", "1979")),
            end_year=int(os.getenv("END_YEAR", "2023")),
            ar_threshold=float(os.getenv("AR_THRESHOLD", "100.0")),
        )

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
