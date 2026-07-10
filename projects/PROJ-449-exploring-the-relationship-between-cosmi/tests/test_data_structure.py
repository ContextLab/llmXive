"""Tests for T006: Data directory structure setup."""
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.data import RAW_DIR, PROCESSED_DIR, CHECKSUMS_FILE, ensure_data_structure

def test_directories_exist():
    """Verify that raw and processed directories exist."""
    ensure_data_structure()
    assert RAW_DIR.exists(), f"Directory {RAW_DIR} does not exist"
    assert RAW_DIR.is_dir(), f"{RAW_DIR} is not a directory"
    
    assert PROCESSED_DIR.exists(), f"Directory {PROCESSED_DIR} does not exist"
    assert PROCESSED_DIR.is_dir(), f"{PROCESSED_DIR} is not a directory"

def test_checksums_file_exists():
    """Verify that checksums.txt exists and is a file."""
    ensure_data_structure()
    assert CHECKSUMS_FILE.exists(), f"File {CHECKSUMS_FILE} does not exist"
    assert CHECKSUMS_FILE.is_file(), f"{CHECKSUMS_FILE} is not a file"

def test_checksums_file_content():
    """Verify checksums.txt contains the expected header."""
    ensure_data_structure()
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# Checksums for downloaded data files will be stored here" in content
