import json
from pathlib import Path

from code.download_data import (
    PARQUET_FILE,
    MP_DESCRIPTORS_FILE,
    EXP_TOF_FILE,
    REQUIRED_COLUMNS_FILE,
    CHECKSUM_FILE,
)

def test_files_exist():
    assert PARQUET_FILE.exists(), "OC20 sample parquet file missing"
    assert MP_DESCRIPTORS_FILE.exists(), "Materials Project descriptors JSON missing"
    assert EXP_TOF_FILE.exists(), "Experimental TOF CSV missing"
    assert REQUIRED_COLUMNS_FILE.exists(), "required_columns.json missing"
    assert CHECKSUM_FILE.exists(), "checksums.txt missing"

def test_checksums_nonempty():
    # Ensure that the checksum file has at least one entry and is parsable
    lines = CHECKSUM_FILE.read_text().strip().splitlines()
    assert len(lines) >= 3, "Expected at least three checksum entries"
    for line in lines:
        parts = line.split()
        assert len(parts) == 2, f"Malformed checksum line: {line}"
        filename, checksum = parts
        assert filename in {
            PARQUET_FILE.name,
            MP_DESCRIPTORS_FILE.name,
            EXP_TOF_FILE.name,
            REQUIRED_COLUMNS_FILE.name,
        }, f"Unexpected filename in checksum file: {filename}"
        assert len(checksum) == 64, "Checksum should be SHA‑256 (64 hex chars)"