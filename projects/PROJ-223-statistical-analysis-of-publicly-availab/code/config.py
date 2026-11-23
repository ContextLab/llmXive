"""
Configuration settings for the Traffic-Weather Severity Analysis pipeline.
Handles paths, random seeds, and environment variables.
"""
import os
from pathlib import Path
from typing import Optional

# Project Root (assumed to be the directory containing this file's parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"

# Random State for reproducibility
RANDOM_SEED = 42

# URLs (can be overridden by environment variables)
FARS_URL = os.getenv(
    "FARS_DATA_URL",
    "https://nhtsa.gov/data/FARS/FARS2022NationalCSV.zip"
)
NOAA_URL = os.getenv(
    "NOAA_DATA_URL",
    "https://huggingface.co/datasets/noaa/isd-hourly/resolve/main/data.parquet"
)

def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_fars_data_url() -> str:
    return FARS_URL

def get_noaa_data_url() -> str:
    return NOAA_URL

def get_output_path(filename: str, sub_dir: str = "processed") -> Path:
    """Construct a full path for an output file."""
    target_dir = PROCESSED_DATA_DIR if sub_dir == "processed" else DATA_DIR / sub_dir
    return target_dir / filename

# Ensure paths exist on import (safe to run multiple times)
ensure_directories()
