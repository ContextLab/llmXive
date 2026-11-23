"""
I/O Utilities for the pipeline.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json(data: Any, file_path: Path) -> None:
    """Save data to a JSON file."""
    ensure_dir(file_path.parent)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def load_json(file_path: Path) -> Any:
    """Load data from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, "r") as f:
        return json.load(f)

def save_csv(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Save a list of dictionaries to a CSV file."""
    ensure_dir(file_path.parent)
    if not data:
        # Create empty file
        file_path.touch()
        return

    import csv
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
