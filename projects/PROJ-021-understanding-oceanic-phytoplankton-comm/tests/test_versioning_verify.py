"""
Integration test for the T011a_verify task.

The test ensures that:
1. The reanalysis NetCDF file is present.
2. Running the versioning script without arguments computes the hash,
   writes it to the state YAML, and exits cleanly.
3. A second run detects a checksum mismatch if the file is tampered with.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from llmxive_toolkit import paths

REANALYSIS_PATH = Path("data/raw/copernicus_global_reanalysis.nc")
STATE_FILE = Path("state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml")
SCRIPT = Path("code/05_versioning_state.py")

def compute_hash(p: Path) -> str:
    sha = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()

@pytest.fixture(scope="module")
def ensure_reanalysis():
    """Ensure the reanalysis file exists; if not, fetch it using the fetch script."""
    if not REANALYSIS_PATH.is_file():
        # Use the existing fetch script to download the real dataset.
        fetch_script = Path("code/01_fetch_reanalysis.py")
        result = subprocess.run(
            [sys.executable, str(fetch_script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Failed to fetch reanalysis data: {result.stderr}"
    assert REANALYSIS_PATH.is_file()
    yield
    # Cleanup state after tests
    if STATE_FILE.is_file():
        STATE_FILE.unlink()

def test_verify_creates_state_entry(ensure_reanalysis):
    """First run should compute hash and create a state entry."""
    # Ensure a clean state file
    if STATE_FILE.is_file():
        STATE_FILE.unlink()

    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script exited with error: {result.stderr}"
    # The script prints the hash; verify it matches the file
    expected_hash = compute_hash(REANALYSIS_PATH)
    assert expected_hash in result.stdout.strip()

    # Verify state file now contains the entry
    assert STATE_FILE.is_file(), "State file was not created"
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    artifact_entry = state.get("artifacts", {}).get(str(REANALYSIS_PATH))
    assert artifact_entry is not None, "Artifact entry missing in state"
    assert artifact_entry["hash"] == expected_hash

def test_checksum_mismatch_detection(ensure_reanalysis):
    """Tamper with the file and ensure the script exits with an error."""
    # First, create a valid state entry
    subprocess.run([sys.executable, str(SCRIPT)], check=True)

    # Corrupt the file (append a byte)
    with open(REANALYSIS_PATH, "ab") as f:
        f.write(b"corruption")

    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    # The script should exit with code 1 and print the specific error message
    assert result.returncode == 1, "Expected non‑zero exit due to checksum mismatch"
    assert "ERROR: Checksum mismatch for reanalysis.nc" in result.stderr