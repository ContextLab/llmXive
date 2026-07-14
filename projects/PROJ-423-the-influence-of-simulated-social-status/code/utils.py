import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def set_seed(seed: int = 42) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

def load_json(path: str) -> Any:
    """Loads a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Any, path: str) -> None:
    """Saves data to a JSON file."""
    ensure_directory(os.path.dirname(path))
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_checksum(path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(file_path: str, checksums: Dict[str, Any]) -> Dict[str, Any]:
    """Updates the checksums dictionary with a new file."""
    checksums["files"][file_path] = calculate_checksum(file_path)
    return checksums

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verifies if a file's checksum matches the expected one."""
    return calculate_checksum(file_path) == expected_checksum

def ensure_directory(path: str) -> None:
    """Creates a directory if it doesn't exist."""
    if path:
        os.makedirs(path, exist_ok=True)

def safe_load_data(path: str) -> Optional[Any]:
    """Safely loads data, returning None if file doesn't exist."""
    if os.path.exists(path):
        return load_json(path)
    return None
