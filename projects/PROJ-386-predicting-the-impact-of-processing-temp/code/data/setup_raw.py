"""
Setup script for T018: Create `data/raw/` directory structure and ensure
raw files are saved with checksums.

This script:
1. Creates the `data/raw/` directory if it doesn't exist (redundant with T001b but ensures readiness).
2. Scans `data/raw/` for any existing files.
3. For each file found, calculates its SHA-256 checksum.
4. Saves a manifest `data/raw/.checksums.json` containing filenames and their hashes.
5. If no files exist, it creates an empty manifest.
6. Integrates with the project's `hash_artifacts.py` logic by reusing the calculation method
   and saving the manifest in the expected format for `state/` tracking.

Usage:
    python code/data/setup_raw.py
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Project root assumption: code/ is one level up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUM_FILE = RAW_DATA_DIR / ".checksums.json"
STATE_DIR = PROJECT_ROOT / "state"

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error hashing {file_path}: {e}", file=sys.stderr)
        return None

def ensure_state_dir():
    """Ensure the state directory exists for manifest storage."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print(f"[*] T018: Setting up raw data directory and checksums at {RAW_DATA_DIR}")
    
    # 1. Ensure directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[+] Directory {RAW_DATA_DIR} is ready.")

    # 2. Scan for files
    files = [f for f in RAW_DATA_DIR.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    checksums = {}
    if files:
        print(f"[*] Found {len(files)} file(s) to hash.")
        for file_path in files:
            print(f"    - Hashing: {file_path.name}")
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                checksums[file_path.name] = file_hash
            else:
                print(f"    [!] Failed to hash {file_path.name}, skipping.")
    else:
        print("[*] No raw data files found yet. Creating empty manifest.")

    # 3. Save manifest locally in data/raw
    manifest_data = {
        "created_at": datetime.utcnow().isoformat(),
        "files": checksums
    }
    
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"[+] Saved local checksum manifest to {CHECKSUM_FILE}")

    # 4. Sync to state/ directory (integrating with T009 logic)
    # We create a specific manifest for the raw data in the state folder
    ensure_state_dir()
    state_manifest_path = STATE_DIR / "raw_data_checksums.json"
    with open(state_manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"[+] Synced manifest to {state_manifest_path}")

    print("[+] T018 Complete: Directory structure verified and checksums recorded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())