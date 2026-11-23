"""
Data schema definitions for the project.
"""
from typing import TypedDict, Required, Optional
import json
from datetime import datetime

class DataVersion(TypedDict):
    """Schema for data version tracking."""
    source_url: Required[str]
    checksum_sha256: Required[str]
    timestamp: Required[str]

class DataVersionFile(TypedDict):
    """Schema for a collection of data versions."""
    files: Required[list[DataVersion]]

def create_empty_data_version() -> dict:
    """Create an empty data version structure."""
    return {"files": []}

def save_data_version_to_file(file_path: str, data_version: dict) -> None:
    """
    Save data version to JSON file.
    
    Args:
        file_path: Path to the output file
        data_version: Data version dictionary to save
    """
    with open(file_path, 'w') as f:
        json.dump(data_version, f, indent=2)

def load_data_version_from_file(file_path: str) -> dict:
    """
    Load data version from JSON file.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        Data version dictionary
    """
    with open(file_path, 'r') as f:
        return json.load(f)
