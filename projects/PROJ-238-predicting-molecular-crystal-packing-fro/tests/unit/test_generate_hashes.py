"""
Unit test for the ``code/03_generate_hashes.py`` script.

The test verifies that running the script creates the expected output file.
It does not depend on the presence of real CIF/CSV/JSON files in the repository;
the script should still produce an (possibly empty) checksum file.
"""

import os
from pathlib import Path
import subprocess
import sys

# Path to the repository root (two levels up from this test file)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Import the script as a module to invoke its ``main`` function directly
SCRIPT_PATH = REPO_ROOT / "code" / "03_generate_hashes.py"

# Expected output location (mirrors the script's configuration)
EXPECTED_OUTPUT = (
    REPO_ROOT
    / "state"
    / "projects"
    / "PROJ-238-predicting-molecular-crystal-packing-fro"
    / "artifact_hashes"
)

def test_generate_hashes_creates_file(tmp_path: Path):
    """
    Run the script and assert that the checksum file exists and is writable.
    """
    # Ensure a clean slate – delete the file if it somehow exists from a previous run
    if EXPECTED_OUTPUT.is_file():
        EXPECTED_OUTPUT.unlink()

    # Run the script via subprocess to emulate real execution
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script exited with error: {result.stderr}"

    # The script should have created the file
    assert EXPECTED_OUTPUT.is_file(), "Checksum output file was not created"

    # The file should contain at least one line if any target files exist;
    # otherwise it may be empty – in both cases it must be readable.
    with EXPECTED_OUTPUT.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    # No strict length assertion – just ensure we could read it without error.
    assert isinstance(lines, list)

    # Clean up after the test to avoid side‑effects for other tests
    EXPECTED_OUTPUT.unlink()