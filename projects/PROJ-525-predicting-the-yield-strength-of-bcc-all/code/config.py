import os
from pathlib import Path
import hashlib
import json
from typing import List, Tuple, Dict, Any
import random

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """Compute a composite checksum for a directory."""
    hasher = hashlib.sha256()
    files = sorted([str(f.relative_to(dir_path)) for f in dir_path.rglob("*") if f.is_file()])
    
    for rel_path in files:
        full_path = dir_path / rel_path
        file_hash = compute_file_checksum(full_path)
        hasher.update(f"{rel_path}:{file_hash}".encode('utf-8'))
    
    return hasher.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not input_path.exists():
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_checksums(stored_checksums: Dict[str, str], base_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify checksums against current file system state.
    Returns (is_valid, list_of_failed_files).
    """
    failed_files = []
    for rel_path, expected_hash in stored_checksums.items():
        full_path = base_path / rel_path
        if not full_path.exists():
            failed_files.append(rel_path)
            continue
        
        actual_hash = compute_file_checksum(full_path)
        if actual_hash != expected_hash:
            failed_files.append(rel_path)
    
    return len(failed_files) == 0, failed_files

# Helper to ensure directories exist if needed by other modules
def ensure_dirs(base_path: Path = None) -> None:
    """Ensure standard project directories exist."""
    if base_path is None:
        base_path = Path.cwd()
    
    dirs = [
        "data/raw", "data/processed", "data/logs",
        "code", "tests", "reports", "state"
    ]
    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)
