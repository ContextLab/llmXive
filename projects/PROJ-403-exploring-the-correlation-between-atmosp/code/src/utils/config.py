"""
Configuration management for the llmXive automated science pipeline.

This module handles environment variable loading, default value resolution,
and provides a centralized configuration object for data paths, thresholds,
and analysis parameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

# Default paths relative to project root
DEFAULT_DATA_DIR = "data"
DEFAULT_PROCESSED_DIR = "data/processed"
DEFAULT_FIGURES_DIR = "figures"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_REPORT_DIR = "report"

# Default thresholds
DEFAULT_AR_THRESHOLD = 250.0  # kg m^-1 s^-1
DEFAULT_LAT_MIN = 20.0
DEFAULT_LAT_MAX = 60.0
DEFAULT_LON_MIN = 100.0
DEFAULT_LON_MAX = 300.0  # 100E to 60W (60W = 300E)

# Environment variable prefix
CONFIG_PREFIX = "LLMXIVE_"


@dataclass
class Config:
    """
    Centralized configuration object for the pipeline.

    Attributes:
        data_dir: Root directory for raw data.
        processed_dir: Directory for processed NetCDF files.
        figures_dir: Directory for output plots.
        logs_dir: Directory for log files.
        report_dir: Directory for final reports.
        ar_threshold: Baseline threshold for AR detection (kg m^-1 s^-1).
        lat_min: Minimum latitude for regional domain.
        lat_max: Maximum latitude for regional domain.
        lon_min: Minimum longitude for regional domain.
        lon_max: Maximum longitude for regional domain.
        start_year: Start year for analysis (default 1979).
        end_year: End year for analysis (default 2023).
        cache_dir: Directory for temporary dask/cache files.
    """
    data_dir: str = DEFAULT_DATA_DIR
    processed_dir: str = DEFAULT_PROCESSED_DIR
    figures_dir: str = DEFAULT_FIGURES_DIR
    logs_dir: str = DEFAULT_LOGS_DIR
    report_dir: str = DEFAULT_REPORT_DIR
    ar_threshold: float = DEFAULT_AR_THRESHOLD
    lat_min: float = DEFAULT_LAT_MIN
    lat_max: float = DEFAULT_LAT_MAX
    lon_min: float = DEFAULT_LON_MIN
    lon_max: float = DEFAULT_LON_MAX
    start_year: int = 1979
    end_year: int = 2023
    cache_dir: str = ".dask_cache"

    # Runtime derived paths (absolute)
    _data_path: Optional[Path] = field(default=None, repr=False)
    _processed_path: Optional[Path] = field(default=None, repr=False)
    _figures_path: Optional[Path] = field(default=None, repr=False)

    def __post_init__(self):
        """Resolve absolute paths after initialization."""
        # Ensure paths are absolute relative to current working directory
        self._data_path = Path(self.data_dir).resolve()
        self._processed_path = Path(self.processed_dir).resolve()
        self._figures_path = Path(self.figures_dir).resolve()

        # Create directories if they don't exist
        self._data_path.mkdir(parents=True, exist_ok=True)
        self._processed_path.mkdir(parents=True, exist_ok=True)
        self._figures_path.mkdir(parents=True, exist_ok=True)

    @property
    def data_path(self) -> Path:
        return self._data_path

    @property
    def processed_path(self) -> Path:
        return self._processed_path

    @property
    def figures_path(self) -> Path:
        return self._figures_path

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return {
            "data_dir": str(self.data_path),
            "processed_dir": str(self.processed_path),
            "figures_dir": str(self.figures_path),
            "logs_dir": self.logs_dir,
            "report_dir": self.report_dir,
            "ar_threshold": self.ar_threshold,
            "lat_min": self.lat_min,
            "lat_max": self.lat_max,
            "lon_min": self.lon_min,
            "lon_max": self.lon_max,
            "start_year": self.start_year,
            "end_year": self.end_year,
        }

    def validate(self) -> bool:
        """
        Validate that all required directories exist and are writable.

        Returns:
            True if valid, False otherwise.
        """
        dirs = [self.data_path, self.processed_path, self.figures_path]
        for d in dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
            if not os.access(d, os.W_OK):
                return False
        return True


def get_config() -> Config:
    """
    Factory function to create a Config object from environment variables.

    Environment variables are prefixed with LLMXIVE_ (e.g., LLMXIVE_DATA_DIR).

    Returns:
        A fully initialized Config object.
    """
    # Helper to get env var with default
    def get_env(key: str, default: Any) -> Any:
        val = os.getenv(f"{CONFIG_PREFIX}{key.upper()}")
        if val is None:
            return default
        # Type conversion
        if isinstance(default, float):
            return float(val)
        if isinstance(default, int):
            return int(val)
        if isinstance(default, bool):
            return val.lower() in ("true", "1", "yes")
        return val

    return Config(
        data_dir=get_env("DATA_DIR", DEFAULT_DATA_DIR),
        processed_dir=get_env("PROCESSED_DIR", DEFAULT_PROCESSED_DIR),
        figures_dir=get_env("FIGURES_DIR", DEFAULT_FIGURES_DIR),
        logs_dir=get_env("LOGS_DIR", DEFAULT_LOGS_DIR),
        report_dir=get_env("REPORT_DIR", DEFAULT_REPORT_DIR),
        ar_threshold=get_env("AR_THRESHOLD", DEFAULT_AR_THRESHOLD),
        lat_min=get_env("LAT_MIN", DEFAULT_LAT_MIN),
        lat_max=get_env("LAT_MAX", DEFAULT_LAT_MAX),
        lon_min=get_env("LON_MIN", DEFAULT_LON_MIN),
        lon_max=get_env("LON_MAX", DEFAULT_LON_MAX),
        start_year=get_env("START_YEAR", 1979),
        end_year=get_env("END_YEAR", 2023),
    )
