"""Data models and fetching package."""

import os
from pathlib import Path

# Define project root relative to this file
_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHECKSUMS_FILE = DATA_DIR / "checksums.txt"

def ensure_data_structure():
    """Create the required data directory structure and initialize checksums file if missing."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    if not CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
            f.write("# Checksums for downloaded data files will be stored here\n")

# Initialize structure immediately upon import to ensure artifacts exist
ensure_data_structure()
