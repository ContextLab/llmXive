import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the code is running from the project root or a subdirectory.
    """
    # If running from code/, go up one level
    current_path = Path(__file__).resolve()
    if current_path.name == "config.py":
        return current_path.parent.parent
    return current_path.parent

def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_project_root() / "data"

def get_processed_data_dir() -> Path:
    """Get the processed data directory path."""
    return get_data_dir() / "processed"

def get_raw_data_dir() -> Path:
    """Get the raw data directory path."""
    return get_data_dir() / "raw"

def get_specs_dir() -> Path:
    """Get the specs directory path."""
    return get_project_root() / "specs" / "001-text-tone-emotional-support"

def get_contracts_dir() -> Path:
    """Get the contracts directory path."""
    return get_specs_dir() / "contracts"
