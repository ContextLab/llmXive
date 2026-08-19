import hashlib
import os
import json
from typing import Dict, List, Optional
from pathlib import Path

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute the checksum of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksum_file(file_path: str, checksum_path: Optional[str] = None) -> str:
    """Generate a checksum file for a given file."""
    if checksum_path is None:
        checksum_path = file_path + ".sha256"
    
    checksum = compute_file_checksum(file_path)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(file_path)}\n")
    return checksum

def verify_checksums(checksum_file_path: str) -> Dict[str, bool]:
    """Verify multiple files against a checksum file."""
    results = {}
    with open(checksum_file_path, 'r') as f:
        for line in f:
            parts = line.strip().split('  ')
            if len(parts) == 2:
                expected_checksum, filename = parts
                file_path = os.path.join(os.path.dirname(checksum_file_path), filename)
                if os.path.exists(file_path):
                    actual_checksum = compute_file_checksum(file_path)
                    results[filename] = (actual_checksum == expected_checksum)
                else:
                    results[filename] = False
    return results

def verify_single_file(file_path: str, checksum: str) -> bool:
    """Verify a single file against a provided checksum."""
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == checksum

def setup_data_directories(base_path: str = "data") -> None:
    """Ensure the required data directory structure exists."""
    dirs = [
        os.path.join(base_path, "raw"),
        os.path.join(base_path, "processed"),
        os.path.join(base_path, "analysis")
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
