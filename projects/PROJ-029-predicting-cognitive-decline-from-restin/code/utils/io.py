"""
Utility functions for I/O operations.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
import pandas as pd

def ensure_dir(directory: Path) -> None:
    """Ensure a directory exists."""
    directory.mkdir(parents=True, exist_ok=True)

def list_bids_subjects(data_dir: Path) -> List[str]:
    """List BIDS subject IDs in a directory."""
    subjects = []
    for item in data_dir.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    return subjects

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary to a JSON file."""
    ensure_dir(file_path.parent)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_bids_subject_data(data_dir: Path, subject_id: str) -> Optional[Dict[str, Any]]:
    """Load data for a specific BIDS subject."""
    sub_dir = data_dir / subject_id
    if not sub_dir.exists():
        return None
    
    data = {'subject_id': subject_id}
    # Scan for JSON files
    for json_file in sub_dir.rglob('*.json'):
        try:
            meta = load_json(json_file)
            data.update(meta)
        except:
            continue
    return data

def save_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Save a DataFrame to CSV."""
    ensure_dir(file_path.parent)
    df.to_csv(file_path, index=False)

def load_csv(file_path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(file_path)

def save_dataframe(df: pd.DataFrame, file_path: Path) -> None:
    """Alias for save_csv."""
    save_csv(df, file_path)

def load_dataframe(file_path: Path) -> pd.DataFrame:
    """Alias for load_csv."""
    return load_csv(file_path)
