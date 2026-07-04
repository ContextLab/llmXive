import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute a checksum for a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (e.g., 'sha256', 'md5').

    Returns:
        Hex digest of the file checksum.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def write_json_artifact(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to serialize to JSON.
        file_path: Destination file path.
        indent: Indentation level for pretty-printing.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

def export_csv(
    data: Union[list[Dict[str, Any]], list[list[Any]]],
    file_path: Union[str, Path],
    fieldnames: Optional[list[str]] = None
) -> None:
    """
    Export data to a CSV file.

    Args:
        data: List of dictionaries or list of lists.
        file_path: Destination file path.
        fieldnames: Column headers if data is a list of dicts.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if not fieldnames:
                fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(f)
            writer.writerows(data)
