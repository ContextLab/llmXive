import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_data_dir
from logging_config import setup_logging, get_logger

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksums_path: Path) -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksums_path: Path) -> None:
    """Save checksums to JSON file."""
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)

def main():
    """Compute SHA-256 checksums for key project files and record in checksums.json."""
    logger = setup_logging()
    logger.info("Starting checksum computation task (T050).")

    project_root = get_project_root()
    checksums_path = project_root / "data" / "checksums.json"
    
    # Load existing checksums to preserve them
    existing_checksums = load_existing_checksums(checksums_path)
    
    # Define files to checksum for T050: data/raw/stimuli.csv
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    
    if not stimuli_path.exists():
        logger.error(f"Stimuli file not found: {stimuli_path}")
        sys.exit(1)
    
    # Compute checksum for stimuli.csv
    stimuli_checksum = compute_sha256(stimuli_path)
    existing_checksums["data/raw/stimuli.csv"] = stimuli_checksum
    
    # Save updated checksums
    save_checksums(existing_checksums, checksums_path)
    
    logger.info(f"Computed SHA-256 for stimuli.csv: {stimuli_checksum}")
    logger.info(f"Updated checksums saved to {checksums_path}")
    print(f"Checksum for data/raw/stimuli.csv: {stimuli_checksum}")
    print(f"Updated data/checksums.json successfully.")

if __name__ == "__main__":
    main()
