import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration management for environment variables and defaults."""
    cds_api_key: str = field(default_factory=lambda: os.getenv("CDS_API_KEY", ""))
    cds_url: str = field(default_factory=lambda: os.getenv("CDS_URL", "https://cds.climate.copernicus.eu/api/v2"))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    ar_threshold: float = float(os.getenv("AR_THRESHOLD", "150.0"))
    lat_min: float = float(os.getenv("LAT_MIN", "20.0"))
    lat_max: float = float(os.getenv("LAT_MAX", "60.0"))
    lon_min: float = float(os.getenv("LON_MIN", "100.0")) # 100E
    lon_max: float = float(os.getenv("LON_MAX", "-60.0")) # 60W
    start_year: int = int(os.getenv("START_YEAR", "1979"))
    end_year: int = int(os.getenv("END_YEAR", "2023"))

def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()
