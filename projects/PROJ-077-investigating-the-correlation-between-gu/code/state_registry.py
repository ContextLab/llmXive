"""
State Registry Module: Checksums and provenance.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from logging_config import get_logger

logger = get_logger("state_registry")

def calculate_file_checksum(path: str, algorithm: str = "sha256") -> str:
    """Calculates checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def scan_raw_data_directory() -> Dict[str, str]:
    """Scans data/raw/ and returns checksums."""
    raw_dir = Path("data/raw")
    checksums = {}
    if not raw_dir.exists():
        return checksums
    for file in raw_dir.glob("*.csv"):
        checksums[file.name] = calculate_file_checksum(str(file))
    return checksums

def initialize_state_registry() -> None:
    """Initializes the state registry YAML."""
    checksums = scan_raw_data_directory()
    state = {
        "artifact_hashes": checksums,
        "timestamp": "now"
    }
    with open("state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml", "w") as f:
        yaml.dump(state, f)

def load_state_registry() -> Dict[str, Any]:
    """Loads the state registry."""
    path = Path("state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml")
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f)

def verify_file_checksums() -> bool:
    """Verifies current files against registry."""
    current = scan_raw_data_directory()
    registry = load_state_registry()
    stored = registry.get("artifact_hashes", {})
    
    if not stored:
        logger.warning("Registry is empty. Cannot verify.")
        return False
    
    for name, stored_hash in stored.items():
        if name not in current:
            logger.error(f"File {name} missing.")
            return False
        if current[name] != stored_hash:
            logger.error(f"Checksum mismatch for {name}.")
            return False
    return True

def main():
    """Entry point."""
    initialize_state_registry()
    if verify_file_checksums():
        print("Checksums verified.")
    else:
        print("Checksums failed or empty.")

if __name__ == "__main__":
    main()
