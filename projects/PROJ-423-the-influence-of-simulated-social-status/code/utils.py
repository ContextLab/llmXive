import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random
import numpy as np

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_json(path: str) -> Dict:
    """Loads a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict, path: str) -> None:
    """Saves a dictionary to a JSON file."""
    ensure_directory(os.path.dirname(path))
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_checksum(file_path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(file_path: str, checksums_file: str = "data/checksums.json") -> None:
    """Updates the checksums.json file with the checksum of the given file."""
    if not os.path.exists(checksums_file):
        checksums = {"files": {}}
    else:
        checksums = load_json(checksums_file)
    
    checksum = calculate_checksum(file_path)
    checksums["files"][file_path] = checksum
    save_json(checksums, checksums_file)

def verify_checksum(file_path: str, checksums_file: str = "data/checksums.json") -> bool:
    """Verifies the checksum of a file against the stored value."""
    if not os.path.exists(checksums_file):
        return False
    
    checksums = load_json(checksums_file)
    if file_path not in checksums["files"]:
        return False
    
    stored_checksum = checksums["files"][file_path]
    current_checksum = calculate_checksum(file_path)
    return stored_checksum == current_checksum

def ensure_directory(path: str) -> None:
    """Ensures a directory exists."""
    if path:
        os.makedirs(path, exist_ok=True)

def safe_load_data(path: str) -> Optional[Any]:
    """Safely loads data from a file, returning None if not found."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def append_to_checksums(file_path: str, checksums_file: str = "data/checksums.json") -> None:
    """Appends a checksum to the file, creating it if necessary."""
    ensure_directory(os.path.dirname(checksums_file))
    if not os.path.exists(checksums_file):
        with open(checksums_file, 'w') as f:
            json.dump({"files": {}}, f)
    update_checksums(file_path, checksums_file)
