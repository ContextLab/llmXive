import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def set_seed(seed: int):
    """Sets random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def load_json(path: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: str):
    """Saves a dictionary to a JSON file."""
    ensure_directory(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_checksum(file_path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(file_path: str, checksums_path: str = "data/checksums.json"):
    """Updates the checksums.json file with the new file's checksum."""
    checksum = calculate_checksum(file_path)
    data = load_json(checksums_path) if os.path.exists(checksums_path) else {"files": {}}
    data["files"][file_path] = checksum
    save_json(data, checksums_path)

def verify_checksum(file_path: str, checksums_path: str = "data/checksums.json") -> bool:
    """Verifies a file's checksum against the stored value."""
    if not os.path.exists(checksums_path):
        return False
    stored = load_json(checksums_path)
    if file_path not in stored.get("files", {}):
        return False
    return calculate_checksum(file_path) == stored["files"][file_path]

def ensure_directory(file_path: str):
    """Ensures the directory for a file path exists."""
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

def safe_load_data(path: str) -> Optional[Any]:
    """Safely loads data from a file, returning None if not found."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def append_checksum_to_file(file_path: str, checksum: str, output_path: str):
    """Appends a checksum to a text file."""
    with open(output_path, 'a') as f:
        f.write(f"{file_path}: {checksum}\n")
