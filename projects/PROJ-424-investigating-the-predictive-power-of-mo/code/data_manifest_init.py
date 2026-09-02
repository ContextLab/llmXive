"""
T004 Implementation: Initialize data manifest and .gitkeep.

This script ensures the existence of the data/raw directory structure,
creates a .gitkeep file to preserve it in version control, and generates
an initial `data/raw/manifest.json` to track checksums for curated experimental data.
"""
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime

# Project root relative to this file (assuming code/data_manifest_init.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW_DIR / "manifest.json"
GITKEEP_PATH = DATA_RAW_DIR / ".gitkeep"

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def ensure_gitkeep() -> None:
    """Ensure .gitkeep exists in data/raw."""
    if not GITKEEP_PATH.exists():
        GITKEEP_PATH.write_text(
            "# This directory tracks curated experimental data.\n"
            "# Do not remove this file; it preserves the directory in version control.\n"
        )
        print(f"Created: {GITKEEP_PATH}")
    else:
        print(f"Exists: {GITKEEP_PATH}")

def init_manifest() -> None:
    """Initialize or update the manifest.json with current state."""
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure .gitkeep exists
    ensure_gitkeep()

    # Scan for existing files to checksum
    existing_files = {}
    for item in DATA_RAW_DIR.iterdir():
        if item.is_file() and item.name not in [".gitkeep", "manifest.json"]:
            checksum = compute_file_hash(item)
            if checksum:
                existing_files[item.name] = {
                    "sha256": checksum,
                    "size_bytes": item.stat().st_size,
                    "last_modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }

    manifest_content = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "description": "Manifest for curated experimental diffusion data (T004).",
        "files": existing_files,
        "notes": [
            "Add new curated data files here and update this manifest with their checksums.",
            "Reference: nist_refs.json (to be created by T006b)."
        ]
    }

    # Write manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_content, f, indent=2)

    print(f"Initialized manifest: {MANIFEST_PATH}")
    if not existing_files:
        print("No data files found yet. Manifest is empty (ready for T006b).")

def main():
    print(f"Running T004: Data Manifest Initialization")
    print(f"Target directory: {DATA_RAW_DIR}")
    init_manifest()
    print("T004 Complete.")

if __name__ == "__main__":
    main()
