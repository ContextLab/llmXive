"""
I/O utilities for BIDS data handling.
Extends existing API to support loading/saving CSVs and JSONs.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
import pandas as pd

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def list_bids_subjects(data_dir: Path) -> List[str]:
    """Return list of subject IDs (sub-*) in a BIDS directory."""
    return [d.name for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]

def load_json(path: Path) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_bids_subject_data(data_dir: Path, subject_id: str) -> Optional[Path]:
    """Locate the main directory for a subject."""
    sub_dir = data_dir / subject_id
    if sub_dir.exists():
        return sub_dir
    return None

def save_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    ensure_dir(path.parent)
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def load_csv(path: Path) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_dataframe(path: Path, df: pd.DataFrame) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=False)

def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)
