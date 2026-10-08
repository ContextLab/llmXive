"""
Verify downloaded datasets against recorded checksums.

This script validates the integrity of raw data files in `data/raw/`
by comparing their SHA-256 hashes against the manifest in `state/artifact_hashes.yaml`.
It ensures that T012 (Data Download) produced valid, uncorrupted artifacts.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any

import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = STATE_DIR / "artifact_hashes.yaml"

def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, str]:
    """Load the checksum manifest from YAML."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest file not found at {MANIFEST_PATH}. "
            "Run T012 (download.py) first to generate the manifest."
        )
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("artifacts", {})

def save_manifest(artifacts: Dict[str, str]) -> None:
    """Save the checksum manifest to YAML."""
    ensure_state_dir()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        yaml.dump({"artifacts": artifacts}, f, default_flow_style=False)

def verify_dataset(file_name: str, expected_hash: str) -> bool:
    """Verify a single dataset file against its expected hash."""
    file_path = DATA_RAW_DIR / file_name
    if not file_path.exists():
        print(f"MISSING: {file_path} does not exist.")
        return False

    actual_hash = compute_file_hash(file_path)
    if actual_hash != expected_hash:
        print(f"MISMATCH: {file_name}")
        print(f"  Expected: {expected_hash}")
        print(f"  Actual:   {actual_hash}")
        return False

    print(f"OK: {file_name} (hash verified)")
    return True

def register_dataset(file_name: str, file_hash: str) -> None:
    """Register a dataset hash in the manifest."""
    manifest = load_manifest()
    manifest[file_name] = file_hash
    save_manifest(manifest)

def main() -> int:
    """
    Main entry point for dataset verification.
    Returns 0 if all checksums match, 1 otherwise.
    """
    if not DATA_RAW_DIR.exists():
        print(f"ERROR: Raw data directory not found at {DATA_RAW_DIR}")
        print("Ensure T012 (download.py) has been run to populate data/raw/.")
        return 1

    try:
        manifest = load_manifest()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    if not manifest:
        print("WARNING: Manifest is empty. No datasets to verify.")
        return 0

    all_valid = True
    for file_name, expected_hash in manifest.items():
        if not verify_dataset(file_name, expected_hash):
            all_valid = False

    if all_valid:
        print("\n✓ All dataset checksums verified successfully.")
        return 0
    else:
        print("\n✗ Verification failed: One or more checksums do not match.")
        return 1

if __name__ == "__main__":
    sys.exit(main())