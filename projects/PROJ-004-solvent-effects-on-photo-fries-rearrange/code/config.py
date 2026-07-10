"""
Configuration and path management for the project.
"""

import os
from pathlib import Path

# Project root is the parent of the code directory
_PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
_RAW_DATA_DIR = _PROJECT_ROOT / "data" / "raw"
_COMPUTE_DATA_DIR = _PROJECT_ROOT / "data" / "compute"
_PROCESSED_DATA_DIR = _PROJECT_ROOT / "data" / "processed"
_CHEMICALS_DIR = _PROJECT_ROOT / "data" / "chemicals"
_FIGURES_DIR = _PROJECT_ROOT / "figures"
_PAPER_DIR = _PROJECT_ROOT / "paper"

def get_raw_data_path() -> Path:
    """Get the path to the raw data directory."""
    return _RAW_DATA_DIR

def get_compute_data_path() -> Path:
    """Get the path to the compute data directory."""
    return _COMPUTE_DATA_DIR

def get_processed_data_path() -> Path:
    """Get the path to the processed data directory."""
    return _PROCESSED_DATA_DIR

def get_chemicals_path() -> Path:
    """Get the path to the chemicals directory."""
    return _CHEMICALS_DIR

def get_figures_path() -> Path:
    """Get the path to the figures directory."""
    return _FIGURES_DIR

def get_paper_path() -> Path:
    """Get the path to the paper directory."""
    return _PAPER_DIR

def ensure_directories() -> None:
    """Create all necessary data directories if they don't exist."""
    for path in [
        _RAW_DATA_DIR,
        _COMPUTE_DATA_DIR,
        _PROCESSED_DATA_DIR,
        _CHEMICALS_DIR,
        _FIGURES_DIR,
        _PAPER_DIR
    ]:
        path.mkdir(parents=True, exist_ok=True)