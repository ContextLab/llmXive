"""
Configuration module for paths, constants, and data URLs.
"""
import os
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "data" / "figures"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

# Random Seed
RANDOM_SEED = 42

# Chunk Size for large file processing (T012b)
CHUNK_SIZE = 50000

# FARS Data Configuration (NHTSA 2022)
# Using the direct CSV link for 2022 data
# Note: The actual URL might change, but this is the standard NHTSA FTP/HTTP structure
FARS_DATA_URL = "https://nhtsa.gov/sites/nhtsa.gov/files/2024-04/fars2022.csv"
# Placeholder checksum - In a real scenario, this would be the SHA256 from NHTSA
# We set it to None for now to allow the download to proceed if the server doesn't provide a checksum file
# If a checksum is known, it should be added here.
FARS_CHECKSUM = None 

# NOAA Data Configuration
NOAA_DATA_URL = "https://huggingface.co/datasets/noaa/isd-hourly/resolve/main/isd-history.csv"
# Fallback or specific dataset path if using a local mirror or different source
# For T013 implementation

def get_fars_data_url() -> str:
    return FARS_DATA_URL

def get_noaa_data_url() -> str:
    return NOAA_DATA_URL

def get_output_path(filename: str, subdir: str = "processed") -> Path:
    if subdir == "raw":
        return RAW_DATA_DIR / filename
    elif subdir == "processed":
        return PROCESSED_DATA_DIR / filename
    elif subdir == "figures":
        return FIGURES_DIR / filename
    elif subdir == "reports":
        return REPORTS_DIR / filename
    else:
        raise ValueError(f"Unknown subdir: {subdir}")

def ensure_directories() -> None:
    """
    Ensure all required data directories exist.
    """
    dirs = [RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, REPORTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")
