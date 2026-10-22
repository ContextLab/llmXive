"""
tests/test_generate_checksums.py
--------------------------------

Integration test for ``src.utils.checksum_all``. The test invokes the
checksum generation script and then verifies that the expected checksum
files exist and contain a 64‑character hexadecimal digest.

The test is deliberately lightweight – it does not validate the digest
against the file contents (that responsibility belongs to the contract
test ``code/tests/test_checksums.py``). Its purpose is to ensure that the
checksum artefacts are created before the contract test runs.
"""

import re
from pathlib import Path

import subprocess
import sys

def test_checksum_files_created():
    """Run the checksum script and assert that the two SHA‑256 files exist."""
    # Execute the checksum generation module.
    result = subprocess.run(
        [sys.executable, "-m", "src.utils.checksum_all"],
        capture_output=True,
        text=True,
    )
    # The script should exit with status 0.
    assert result.returncode == 0, f"Checksum script failed: {result.stderr}"

    # Expected checksum file locations.
    raw_checksum = Path("data/checksums/raw_defects.sha256")
    features_checksum = Path("data/checksums/features.sha256")

    # Both files must exist after the script runs.
    assert raw_checksum.is_file(), "Missing raw_defects.sha256"
    assert features_checksum.is_file(), "Missing features.sha256"

    # Verify that each file contains a valid 64‑character hex string.
    hex_pattern = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)

    for checksum_path in (raw_checksum, features_checksum):
        content = checksum_path.read_text().strip()
        assert hex_pattern.fullmatch(content), (
            f"Checksum file {checksum_path} does not contain a valid SHA‑256 digest"
        )