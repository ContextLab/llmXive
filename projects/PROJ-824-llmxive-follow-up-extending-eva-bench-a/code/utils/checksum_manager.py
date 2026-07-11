import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories
from logging_config import setup_logging

logger = setup_logging(__name__)

CHECKSUMS_FILE = Path("data/checksums.json")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_checksums() -> Dict[str, Any]:
    """Load checksums.json, initializing if missing."""
    ensure_directories([CHECKSUMS_FILE.parent])
    if not CHECKSUMS_FILE.exists():
        data = {"files": []}
        save_checksums(data)
        return data
    
    with open(CHECKSUMS_FILE, "r") as f:
        data = json.load(f)
    
    if "files" not in data or not isinstance(data["files"], list):
        logger.warning("Invalid checksums.json structure. Resetting.")
        data = {"files": []}
        save_checksums(data)
    
    return data

def save_checksums(data: Dict[str, Any]) -> None:
    """Save checksums to disk."""
    ensure_directories([CHECKSUMS_FILE.parent])
    with open(CHECKSUMS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_file_checksum(file_path: Path) -> None:
    """Compute and store SHA-256 for a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    data = load_checksums()
    file_path_str = str(file_path)
    
    # Remove existing entry if present
    data["files"] = [
        entry for entry in data["files"] 
        if entry["path"] != file_path_str
    ]
    
    # Add new entry
    sha256 = compute_sha256(file_path)
    data["files"].append({
        "path": file_path_str,
        "sha256": sha256
    })
    
    save_checksums(data)
    logger.info(f"Checksum added for {file_path}: {sha256[:16]}...")

def verify_checksum(file_path: Path) -> bool:
    """Verify file against stored checksum."""
    data = load_checksums()
    file_path_str = str(file_path)
    
    stored_entry = next(
        (entry for entry in data["files"] if entry["path"] == file_path_str),
        None
    )
    
    if not stored_entry:
        logger.warning(f"No stored checksum for {file_path}")
        return False
    
    current_hash = compute_sha256(file_path)
    return current_hash == stored_entry["sha256"]

def init_checksums() -> None:
    """Initialize empty checksums.json."""
    data = {"files": []}
    save_checksums(data)
    logger.info("Initialized empty data/checksums.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            init_checksums()
        elif sys.argv[1] == "add" and len(sys.argv) > 2:
            add_file_checksum(Path(sys.argv[2]))
        elif sys.argv[1] == "verify" and len(sys.argv) > 2:
            path = Path(sys.argv[2])
            if verify_checksum(path):
                print(f"OK: {path}")
            else:
                print(f"FAIL: {path}")
                sys.exit(1)
        else:
            print("Usage: python checksum_manager.py [init|add <path>|verify <path>]")
            sys.exit(1)
    else:
        init_checksums()
