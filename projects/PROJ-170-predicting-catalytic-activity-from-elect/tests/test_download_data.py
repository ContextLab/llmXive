import os
import sys
import json
import hashlib
from pathlib import Path

import pytest

# Ensure the code directory is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import (
    PARQUET_FILE,
    MP_DESCRIPTORS_FILE,
    EXP_TOF_FILE,
    REQUIRED_COLUMNS_FILE,
    CHECKSUM_FILE,
    verify_downloaded_data,
    compute_file_hash,
)

def test_files_exist_and_nonempty(tmp_path):
    # Run the main function to generate files
    from download_data import main
    exit_code = main()
    assert exit_code == 0, "download_data script failed"

    # Verify each expected file exists
    for path in [PARQUET_FILE, MP_DESCRIPTORS_FILE, EXP_TOF_FILE, REQUIRED_COLUMNS_FILE, CHECKSUM_FILE]:
        assert path.exists(), f"{path} does not exist"
        assert path.stat().st_size > 0, f"{path} is empty"

    # Verify checksum entries are recorded
    checksums = {}
    with open(CHECKSUM_FILE, "r") as f:
        for line in f:
            name, val = line.strip().split()
            checksums[name] = val

    for path in [PARQUET_FILE, MP_DESCRIPTORS_FILE, EXP_TOF_FILE, REQUIRED_COLUMNS_FILE]:
        assert path.name in checksums, f"{path.name} missing from checksum file"
        # Verify the stored checksum matches the actual file hash
        actual_hash = compute_file_hash(path)
        assert checksums[path.name] == actual_hash, f"Checksum mismatch for {path.name}"

    # Verify the helper function works
    assert verify_downloaded_data(PARQUET_FILE) is True