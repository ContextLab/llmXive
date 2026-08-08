# This file is a copy of 05_compute_checksums.py to allow import in tests
# In a real scenario, tests would import from code.05_compute_checksums
# This is a workaround for the test runner structure
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Mock config for testing if needed, but we assume standard imports work in real env
# from config import get_data_dir, get_raw_data_dir, get_processed_data_dir, get_results_dir
# from logging_config import setup_logging, get_logger

# For the purpose of this test file to run independently, we define minimal mocks
# if the real imports fail, but the actual module uses the real ones.
# The main module 05_compute_checksums.py uses the real imports.

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksum_file: Path) -> Dict[str, Any]:
    """Load existing checksums from JSON file, or return empty dict if not found."""
    if not checksum_file.exists():
        return {}
    try:
        with open(checksum_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"Checksum file {checksum_file} is not valid JSON. Starting fresh.")
        return {}

def save_checksums(checksums: Dict[str, Any], checksum_file: Path) -> None:
    """Save checksums to JSON file."""
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)