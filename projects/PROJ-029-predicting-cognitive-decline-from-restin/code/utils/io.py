import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
import pandas as pd

def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def list_bids_subjects(bids_dir: Path) -> List[str]:
    """List all subject IDs in a BIDS directory."""
    subjects = []
    for item in bids_dir.iterdir():
        if item.is_dir() and item.name.startswith('sub-'):
            subjects.append(item.name)
    return sorted(subjects)

def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: Path):
    """Save data to JSON file."""
    ensure_dir(Path(path).parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_bids_subject_data(bids_dir: Path, subject_id: str) -> Optional[Dict[str, Any]]:
    """Load all data for a specific subject."""
    subject_path = bids_dir / subject_id
    if not subject_path.exists():
        return None
    
    data = {'subject_id': subject_id, 'files': []}
    for root, dirs, files in os.walk(subject_path):
        for file in files:
            file_path = Path(root) / file
            data['files'].append(str(file_path))
    return data

def save_csv(data: List[Dict], path: str):
    """Save list of dicts to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def load_csv(path: str) -> pd.DataFrame:
    """Load CSV to DataFrame."""
    return pd.read_csv(path)

def save_dataframe(df: pd.DataFrame, path: str):
    """Save DataFrame to CSV."""
    df.to_csv(path, index=False)

def load_dataframe(path: str) -> pd.DataFrame:
    """Load CSV to DataFrame."""
    return pd.read_csv(path)
