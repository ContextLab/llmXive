"""
T018: Add checksum generation for data/ground_truth/manual_labels.csv 
and record in state/checksums.json.

This script calculates the SHA-256 checksum of the ground truth manual labels file
and stores it in a state tracking file for integrity verification.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

DATA_GROUND_TRUTH = project_root / "data" / "ground_truth"
STATE_DIR = project_root / "state"
MANUAL_LABELS_FILE = DATA_GROUND_TRUTH / "manual_labels.csv"
CHECKSUMS_FILE = STATE_DIR / "checksums.json"


def setup_output_directories():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_GROUND_TRUTH.mkdir(parents=True, exist_ok=True)


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_existing_checksums() -> dict:
    """Load existing checksums if the file exists, otherwise return empty dict."""
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checksums(checksums: dict):
    """Save checksums dictionary to JSON file."""
    with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)


def generate_checksum_for_manual_labels():
    """
    Main logic to generate checksum for manual_labels.csv and save to state/checksums.json.
    
    Returns:
        dict: The updated checksums dictionary.
    """
    setup_output_directories()
    
    if not MANUAL_LABELS_FILE.exists():
        raise FileNotFoundError(
            f"Ground truth file not found at {MANUAL_LABELS_FILE}. "
            "Ensure T017a (ground truth selection) has been completed first."
        )
    
    file_hash = calculate_file_checksum(MANUAL_LABELS_FILE)
    
    existing_checksums = load_existing_checksums()
    
    # Update or add the checksum entry
    existing_checksums["manual_labels.csv"] = {
        "path": str(MANUAL_LABELS_FILE.relative_to(project_root)),
        "algorithm": "sha256",
        "hash": file_hash,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "file_size_bytes": MANUAL_LABELS_FILE.stat().st_size
    }
    
    save_checksums(existing_checksums)
    
    print(f"Checksum generated for: {MANUAL_LABELS_FILE}")
    print(f"Algorithm: SHA-256")
    print(f"Hash: {file_hash}")
    print(f"Saved to: {CHECKSUMS_FILE}")
    
    return existing_checksums


def main():
    """Entry point for the script."""
    try:
        generate_checksum_for_manual_labels()
        print("Checksum generation completed successfully.")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during checksum generation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())