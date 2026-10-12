"""
Integration test for the verify_quality_run script.

The test executes the script as a subprocess, checks that it exits
successfully, and verifies that the expected results file is created
with a parsable floating‑point value.
"""

import subprocess
import sys
from pathlib import Path

def test_verify_quality_run_creates_result_file():
    """
    Run the verification script and ensure it writes the mean FD file.
    """
    # Execute the script using the same interpreter that runs the tests
    result = subprocess.run(
        [sys.executable, "code/data/verify_quality_run.py"],
        capture_output=True,
        text=True,
    )
    # The script should exit with a zero status code
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected output file location
    output_file = Path("data/results/mean_fd.txt")
    assert output_file.is_file(), "Mean FD result file was not created"

    # Verify the file contains a valid float
    try:
        value = float(output_file.read_text().strip())
    except ValueError as e:
        raise AssertionError("Mean FD file does not contain a valid float") from e

    # Basic sanity check: FD cannot be negative
    assert value >= 0.0, "Mean FD should be non‑negative"