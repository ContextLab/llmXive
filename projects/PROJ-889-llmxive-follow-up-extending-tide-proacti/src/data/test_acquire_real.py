"""
src/data/test_acquire_real.py

Pytest integration test for the T001 data acquisition script.
"""

import subprocess
import sys
from pathlib import Path
import csv

import pytest
from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_acquire_real():
    """Execute the acquisition script and verify its outputs."""
    result = subprocess.run(
        [sys.executable, "-m", "src.data.acquire_real"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"

    # Verify CSV exists and has >=200 rows (excluding header)
    csv_path = paths.data("raw", "tide.csv")
    assert csv_path.is_file(), f"CSV not found at {csv_path}"
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert len(rows) > 1, "CSV appears to be empty (no header row)."
    data_rows = len(rows) - 1
    assert data_rows >= 200, f"CSV contains only {data_rows} data rows; expected >= 200."

    # Verify checksum manifest exists
    sha_path = paths.data("raw", "tide.sha256")
    assert sha_path.is_file(), f"Checksum file not found at {sha_path}"
    
    # Verify log exists
    log_path = paths.data("logs", "acquire_real.log")
    assert log_path.is_file(), f"Log file not found at {log_path}"