"""
Utility functions for CSV reading/writing and checksum validation.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TextIO, BinaryIO

def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_file_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify checksum of a file."""
    return calculate_file_checksum(file_path, algorithm) == expected_checksum

def read_csv_as_dicts(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read CSV file as list of dictionaries."""
    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_dicts_to_csv(file_path: Union[str, Path], data: List[Dict[str, Any]]):
    """Write list of dictionaries to CSV file."""
    if not data:
        return
    fieldnames = data[0].keys()
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Read JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)

def write_json(file_path: Union[str, Path], data: Dict[str, Any]):
    """Write data to JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def generate_checksum_file(file_path: Union[str, Path], checksum_path: Union[str, Path]):
    """Generate checksum file for a given file."""
    checksum = calculate_file_checksum(file_path)
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {os.path.basename(file_path)}\n")

def verify_checksum_file(checksum_path: Union[str, Path]) -> bool:
    """Verify checksum file."""
    with open(checksum_path, "r") as f:
        line = f.readline().strip()
        expected, filename = line.split("  ")
    return verify_file_checksum(Path(checksum_path).parent / filename, expected)
