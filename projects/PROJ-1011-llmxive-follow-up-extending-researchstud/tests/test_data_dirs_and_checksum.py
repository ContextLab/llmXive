"""
Unit test for task T004.

Verifies that the required data directories and the CHECKSUMS manifest
exist after running the `create_data_dirs.py` script.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths


def test_data_dirs_and_checksum(tmp_path):
    """
    Run the directory-creation script and assert that the expected
    directories and manifest file exist.
    """
    # Execute the script (it uses project-relative paths, so we run it from the repo root)
    result = subprocess.run(
        ["python", "code/create_data_dirs.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected directories
    for subdir in ("raw", "processed", "results"):
        dir_path = paths.data(subdir)
        assert dir_path.is_dir(), f"Missing data directory: {dir_path}"

    # Expected manifest file
    checksum_path = paths.data("CHECKSUMS")
    assert checksum_path.is_file(), f"Missing CHECKSUMS manifest: {checksum_path}"