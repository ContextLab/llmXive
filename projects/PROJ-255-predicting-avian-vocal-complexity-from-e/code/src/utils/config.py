import os
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    current_file = Path(__file__).resolve()
    # Assuming structure: code/src/utils/config.py -> project root is 3 levels up
    return current_file.parent.parent.parent

def get_data_dir() -> Path:
    """Return the path to the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Return the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_interim_data_dir() -> Path:
    """Return the path to the interim data directory."""
    return get_data_dir() / "interim"

def get_processed_data_dir() -> Path:
    """Return the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_figures_dir() -> Path:
    """Return the path to the figures directory."""
    return get_data_dir() / "figures"

def ensure_directories() -> None:
    """Create all required data directories if they do not exist."""
    dirs = [
        get_raw_data_dir(),
        get_interim_data_dir(),
        get_processed_data_dir(),
        get_figures_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
