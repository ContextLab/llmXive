"""
Script to initialize the verified_data_sources.json file.
This file contains the expected source IDs and checksums for DreamX-World and ScanNet.
It is used to verify data integrity before any processing begins.
"""

import json
import hashlib
import os
import sys
from pathlib import Path

# Define the project root relative to this script location
# Assuming scripts/ is at repo root or project root level
SCRIPT_DIR = Path(__file__).parent.resolve()
# Try to find the project root by looking for a marker or going up
# For this specific project, we assume the script is at the repo root or project root
# The task says "Run from repo root", so we assume cwd is repo root.
# We will write the file to the current working directory (repo root) or a specific config dir if needed.
# Based on T000b description: "Create `verified_data_sources.json` ... containing expected source IDs and checksums".
# It doesn't specify a subdirectory, so we place it at the project root (cwd).

OUTPUT_FILE = Path("verified_data_sources.json")

# Define the expected sources and their checksums (SHA-256)
# Note: These are placeholders for the actual checksums. In a real scenario,
# these would be the actual checksums of the downloaded datasets.
# Since we cannot download the real datasets in this context, we define the structure.
# The script will generate the file with these expected values.
# If the real checksums are known, they should be updated here.
# For the purpose of this task, we define the schema and structure.
# The actual checksums would be computed after downloading the real data.
# We will use a placeholder checksum for demonstration, but the structure is correct.

# Placeholder checksums - in reality, these must be computed from the real data
# DreamX-World: A hypothetical dataset ID and checksum
DREAMX_WORLD_ID = "dreamx-world-v1.0"
DREAMX_WORLD_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # SHA-256 of empty string as placeholder

# ScanNet: A hypothetical dataset ID and checksum
SCANNET_ID = "scannet-v2"
SCANNET_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # SHA-256 of empty string as placeholder

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_verified_sources_file():
    """Generate the verified_data_sources.json file if it doesn't exist."""
    if OUTPUT_FILE.exists():
        print(f"Warning: {OUTPUT_FILE} already exists. Skipping generation.")
        return

    data = {
        "version": "1.0",
        "sources": {
            "dreamx_world": {
                "id": DREAMX_WORLD_ID,
                "checksum": DREAMX_WORLD_CHECKSUM,
                "description": "DreamX-World dataset for 3D consistency evaluation",
                "type": "video_3d"
            },
            "scannet": {
                "id": SCANNET_ID,
                "checksum": SCANNET_CHECKSUM,
                "description": "ScanNet dataset as fallback for 3D consistency evaluation",
                "type": "scan_3d"
            }
        },
        "generated_at": "2023-10-27T10:00:00Z", # Placeholder timestamp
        "note": "Checksums are placeholders. Update with actual checksums after downloading real data."
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Successfully created {OUTPUT_FILE}")

def main():
    """Main entry point."""
    generate_verified_sources_file()

if __name__ == "__main__":
    main()
