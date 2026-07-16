import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute a checksum for a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def write_json_artifact(data: Any, file_path: str, indent: int = 2) -> None:
    """
    Write a JSON artifact to disk.

    Args:
        data: Data to serialize to JSON.
        file_path: Path to write the JSON file.
        indent: Indentation level for pretty printing.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)

def export_csv(data: List[Dict[str, Any]], file_path: str, fieldnames: Optional[List[str]] = None) -> None:
    """
    Export a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to export.
        file_path: Path to the output CSV file.
        fieldnames: Optional list of column names. If None, keys from the first
                    dictionary are used.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # Write empty file if no data
        with open(path, "w", newline="", encoding="utf-8") as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
