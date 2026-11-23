"""Data modules for fetching, aligning, and processing cosmic ray data."""
import os
from pathlib import Path

# Define data directory structure
BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHECKSUMS_FILE = BASE_DIR / "data" / "checksums.txt"

def ensure_data_structure():
    """Ensure the required data directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if not CHECKSUMS_FILE.exists():
        CHECKSUMS_FILE.touch()

# Initialize structure on import
ensure_data_structure()

from code.data.models import CosmicRayFlux, SolarActivityIndex, CompositionRatio
from code.data.fetch_ams02 import fetch_species_data
from code.data.fetch_noaa import fetch_noaa_sunspots
from code.data.align_data import load_flux_data, load_solar_data, flag_gaps, merge_datasets
from code.data.preprocess import calculate_composition_ratios

__all__ = [
    "RAW_DIR",
    "PROCESSED_DIR",
    "CHECKSUMS_FILE",
    "ensure_data_structure",
    "CosmicRayFlux",
    "SolarActivityIndex",
    "CompositionRatio",
    "fetch_species_data",
    "fetch_noaa_sunspots",
    "load_flux_data",
    "load_solar_data",
    "flag_gaps",
    "merge_datasets",
    "calculate_composition_ratios",
]
