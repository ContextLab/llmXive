"""
Integration test for the QM9 download script (Task T004).

The test invokes the script programmatically and checks that:

1. ``data/raw/qm9_subset.parquet`` is created and is non‑empty.
2. ``data/raw/checksums.json`` contains a ``qm9_subset`` entry whose
   ``hash`` matches the SHA‑256 of the generated parquet file.

The test is deliberately lightweight – it uses the default subset size
(100 k rows) which fits comfortably within the CI runner limits.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

import pytest

# Path helpers
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "code" / "data" / "download.py"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PARQUET_PATH = RAW_DIR / "qm9_subset.parquet"
CHECKSUMS_PATH = RAW_DIR / "checksums.json"

@pytest.fixture(scope="module")
def run_download_script():
    """Run the download script once for the whole test module."""
    # Ensure a clean state
    if PARQUET_PATH.is_file():
        PARQUET_PATH.unlink()
    if CHECKSUMS_PATH.is_file():
        CHECKSUMS_PATH.unlink()

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dataset", "qm9", "--output", str(RAW_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    # Propagate any unexpected failure
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    yield
    # Cleanup after tests
    if PARQUET_PATH.is_file():
        PARQUET_PATH.unlink()
    if CHECKSUMS_PATH.is_file():
        CHECKSUMS_PATH.unlink()

def test_parquet_created(run_download_script):
    """The parquet file must exist and contain rows."""
    assert PARQUET_PATH.is_file(), "Parquet file was not created."
    df = pd.read_parquet(PARQUET_PATH)
    assert not df.empty, "Parquet file is empty."
    # Basic sanity check – at least 10 000 rows should be present
    assert len(df) >= 10_000, "Parquet file contains fewer rows than expected."

def test_checksum_entry(run_download_script):
    """checksums.json must contain a matching entry for the parquet file."""
    assert CHECKSUMS_PATH.is_file(), "checksums.json was not created."

    with CHECKSUMS_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "qm9_subset" in manifest, "qm9_subset entry missing in checksums.json."

    entry = manifest["qm9_subset"]
    assert "hash" in entry, "Checksum entry lacks 'hash' field."
    assert entry["file"] == "qm9_subset.parquet", "Filename mismatch in checksum entry."

    # Compute the hash independently and compare
    from hashlib import sha256

    def compute_hash(p):
        h = sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    expected_hash = compute_hash(PARQUET_PATH)
    assert entry["hash"] == expected_hash, "Recorded checksum does not match actual file hash."