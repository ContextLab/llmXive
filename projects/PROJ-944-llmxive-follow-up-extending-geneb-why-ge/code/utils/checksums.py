"""
Checksum utility for the llmXive pipeline.
Computes SHA-256 hashes for files in data/raw/ and data/processed/
and prepares a state snippet for state/...yaml.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any

import yaml

# Project root relative to this file's location logic
# Assuming code/utils/checksums.py is at code/utils/
# Project root is two levels up: code/utils/../..
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def scan_directory_for_hashes(directory: Path) -> Dict[str, str]:
    """
    Scan a directory recursively for files and compute their SHA-256 hashes.
    Returns a dictionary mapping relative file paths to their hashes.
    """
    if not directory.exists():
        return {}

    hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            # Store path relative to the scanned directory for readability
            relative_path = file_path.relative_to(directory)
            try:
                file_hash = compute_sha256(file_path)
                hashes[str(relative_path)] = file_hash
            except Exception as e:
                # Log error but continue scanning
                print(f"Warning: Could not compute hash for {file_path}: {e}")

    return hashes

def generate_checksum_report() -> Dict[str, Any]:
    """
    Generate a checksum report for data/raw/ and data/processed/.
    Returns a dictionary suitable for saving to state/...yaml.
    """
    raw_hashes = scan_directory_for_hashes(DATA_RAW_DIR)
    processed_hashes = scan_directory_for_hashes(DATA_PROCESSED_DIR)

    report = {
        "artifact_hashes": {
            "data/raw": raw_hashes,
            "data/processed": processed_hashes
        }
    }
    return report

def save_checksum_state(output_path: Path):
    """
    Save the checksum report to a YAML file in the state directory.
    """
    report = generate_checksum_report()
    with open(output_path, "w") as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    print(f"Checksum state saved to: {output_path}")

def main():
    """Main entry point for checksum generation."""
    # Define the output file path based on project ID
    project_id = "PROJ-944-llmxive-follow-up-extending-geneb-why-ge"
    output_file = STATE_DIR / f"{project_id}_checksums.yaml"

    print(f"Scanning {DATA_RAW_DIR} and {DATA_PROCESSED_DIR} for SHA-256 hashes...")
    save_checksum_state(output_file)

    # Optional: Print a summary
    report = generate_checksum_report()
    total_files = (
        len(report["artifact_hashes"]["data/raw"]) +
        len(report["artifact_hashes"]["data/processed"])
    )
    print(f"Total files processed: {total_files}")

if __name__ == "__main__":
    main()
