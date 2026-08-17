"""
Configuration management for the Avian Vocal Complexity project.

This module defines global constants, paths, seeds, and thresholds
used throughout the pipeline.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Global Seeds for reproducibility
SEED = 42
RANDOM_SEED = 42

# Directory Paths
PATHS: Dict[str, str] = {
    'RAW': 'data/raw',
    'INTERIM': 'data/interim',
    'PROCESSED': 'data/processed',
    'FIGURES': 'data/figures'
}

# Thresholds and Parameters
THRESHOLDS: Dict[str, Any] = {
    'SNR_DEFAULT': 10,
    'INTERPOLATION_MAX_KM': 50,
    'MISSING_THRESHOLD_PERCENT': 10
}

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root.
    Assumes the project root is two levels up from this file's location.
    """
    # This file is at code/src/utils/config.py
    # Project root is code/
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def get_data_dir() -> Path:
    """Returns the absolute path to the data directory."""
    return get_project_root() / 'data'

def get_raw_data_dir() -> Path:
    """Returns the absolute path to the raw data directory."""
    return get_data_dir() / PATHS['RAW']

def get_interim_data_dir() -> Path:
    """Returns the absolute path to the interim data directory."""
    return get_data_dir() / PATHS['INTERIM']

def get_processed_data_dir() -> Path:
    """Returns the absolute path to the processed data directory."""
    return get_data_dir() / PATHS['PROCESSED']

def get_figures_dir() -> Path:
    """Returns the absolute path to the figures directory."""
    return get_data_dir() / PATHS['FIGURES']

def ensure_directories() -> None:
    """
    Ensures all required data directories exist.
    Creates them if they do not exist.
    """
    for dir_name in PATHS.values():
        dir_path = get_data_dir() / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def get_snr_threshold() -> float:
    """Returns the default SNR threshold for filtering."""
    return THRESHOLDS['SNR_DEFAULT']

def get_interpolation_max_km() -> float:
    """Returns the maximum distance (km) for noise interpolation."""
    return THRESHOLDS['INTERPOLATION_MAX_KM']

def get_missing_threshold_percent() -> float:
    """Returns the percentage threshold for missing data warnings."""
    return THRESHOLDS['MISSING_THRESHOLD_PERCENT']