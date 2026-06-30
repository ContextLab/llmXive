"""
Input/Output utilities for BIDS data handling and directory management.
"""
import os
from pathlib import Path
from typing import List

import json
import csv
import pandas as pd

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_ARTIFACTS_DIR

def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    Returns the Path object.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

def list_bids_subjects(data_dir: Path) -> List[str]:
    """
    Scan a BIDS directory and return a list of subject IDs.
    Expects standard BIDS structure: sub-<label>/
    """
    subjects = []
    if not data_dir.exists():
        return subjects

    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            subjects.append(item.name)
    
    # Sort for reproducibility
    subjects.sort()
    return subjects

def load_json(path: Path) -> dict:
    """
    Safely load a JSON file.
    """
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: dict, path: Path) -> None:
    """
    Safely save a dictionary to a JSON file.
    """
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_bids_subject_data(subject_dir: Path) -> dict:
    """
    Load BIDS metadata for a subject.
    
    Args:
        subject_dir: Path to the subject directory (e.g., data/raw/sub-01)
        
    Returns:
        Dictionary containing subject metadata and available files.
    """
    metadata = {
        "subject_id": subject_dir.name,
        "files": [],
        "json_sidecars": {}
    }
    
    if not subject_dir.exists():
        return metadata
        
    for item in subject_dir.rglob("*"):
        if item.is_file():
            metadata["files"].append(str(item.relative_to(subject_dir)))
            if item.suffix == ".json":
                try:
                    metadata["json_sidecars"][str(item.relative_to(subject_dir))] = load_json(item)
                except Exception:
                    pass
                    
    return metadata

def save_csv(data: List[dict], path: Path) -> None:
    """
    Save a list of dictionaries to a CSV file.
    """
    ensure_dir(path.parent)
    if not data:
        # Write empty file with no rows
        with open(path, 'w', newline='') as f:
            pass
        return
        
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def load_csv(path: Path) -> List[dict]:
    """
    Load a CSV file into a list of dictionaries.
    """
    if not path.exists():
        return []
        
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    """
    Save a pandas DataFrame to a CSV file.
    """
    ensure_dir(path.parent)
    df.to_csv(path, index=False)

def load_dataframe(path: Path) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    """
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
