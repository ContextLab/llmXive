"""
Configuration management for paths, seeds, and constants.
"""
import os
from pathlib import Path
from typing import Optional

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Seeds
SEED = 42
RANDOM_SEED = 42

# Constants
DEFAULT_SNR_THRESHOLD = 10.0  # dB
MIN_RECORDINGS_PER_SPECIES = 5
NOISE_LEVELS = {
    'urban': 60,
    'rural': 40,
    'wild': 30
}

def get_project_root() -> Path:
    """Returns the project root directory."""
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    """Returns the data directory."""
    return _PROJECT_ROOT / 'data'

def get_raw_data_dir() -> Path:
    """Returns the raw data directory."""
    return get_data_dir() / 'raw'

def get_interim_data_dir() -> Path:
    """Returns the interim data directory."""
    return get_data_dir() / 'interim'

def get_processed_data_dir() -> Path:
    """Returns the processed data directory."""
    return get_data_dir() / 'processed'

def get_figures_dir() -> Path:
    """Returns the figures directory."""
    return get_data_dir() / 'figures'

def ensure_directories():
    """Creates all necessary data directories if they don't exist."""
    dirs = [
        get_raw_data_dir(),
        get_interim_data_dir(),
        get_processed_data_dir(),
        get_figures_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
