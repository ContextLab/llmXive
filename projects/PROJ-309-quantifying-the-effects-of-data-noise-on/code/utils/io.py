import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to compute checksum for.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def write_json_artifact(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a dictionary to a JSON file.

    Args:
        data: Dictionary to serialize to JSON.
        file_path: Path where the JSON file will be written.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def export_csv(data: List[Dict[str, Any]], file_path: str, fieldnames: Optional[List[str]] = None) -> None:
    """
    Export a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries where each dict represents a row.
        file_path: Path where the CSV file will be written.
        fieldnames: Optional list of column names. If None, keys from the first
                    dictionary are used.
    """
    if not data:
        raise ValueError("Cannot export empty data list to CSV")

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
