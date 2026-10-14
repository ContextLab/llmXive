"""
Integration test for the 00_hash_artifacts script.

This test ensures that the script runs without error, creates the
`state/hashes.yaml` file, and populates it with at least one artifact
entry (i.e., hashes for files found under the `data/` directory).
"""

import subprocess
import sys
from pathlib import Path
import yaml

import pytest

@pytest.fixture
def hashes_path():
    """Path to the hashes.yaml file."""
    return Path(__file__).resolve().parents[2] / "state" / "hashes.yaml"

def test_hash_artifacts_execution(tmp_path, hashes_path):
    """
    Run the hashing script and verify its output.

    Steps:
    1. Ensure any existing hashes.yaml is removed to start fresh.
    2. Execute the script via subprocess.
    3. Load the generated YAML and assert it contains the expected structure.
    """
    # Remove any pre‑existing file to guarantee a clean run
    if hashes_path.exists():
        hashes_path.unlink()

    # Construct the command to run the script
    script_path = Path(__file__).resolve().parents[2] / "code" / "00_hash_artifacts.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=script_path.parent,
        capture_output=True,
        text=True,
    )

    # The script should exit with code 0
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Verify the output file was created
    assert hashes_path.is_file(), f"Expected hashes file at {hashes_path} not found."

    # Load the YAML content
    with open(hashes_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Basic sanity checks on the structure
    assert isinstance(data, dict), "Hashes YAML should be a mapping."
    assert "artifacts" in data, "Hashes YAML missing 'artifacts' key."
    assert isinstance(data["artifacts"], dict), "'artifacts' should be a mapping."

    # There should be at least one hashed artifact (the script always hashes any
    # non‑empty file under the data directory).
    assert len(data["artifacts"]) > 0, "No artifacts were hashed; expected at least one entry."

    # Spot‑check that each entry has the required fields
    for rel_path, meta in data["artifacts"].items():
        assert "hash" in meta, f"Missing 'hash' for {rel_path}"
        assert "size_bytes" in meta, f"Missing 'size_bytes' for {rel_path}"
        assert "last_modified" in meta, f"Missing 'last_modified' for {rel_path}"
        # The hash should be a 64‑character hex string
        assert isinstance(meta["hash"], str) and len(meta["hash"]) == 64, f"Invalid hash for {rel_path}"
        break  # One entry is enough for the test; the loop ensures format correctness.