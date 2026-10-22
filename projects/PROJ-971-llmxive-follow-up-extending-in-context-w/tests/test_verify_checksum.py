"""
test_verify_checksum.py

Simple test that imports the verification script and runs its ``main``
function. The test will pass if the script exits with status 0,
which indicates that the checksum of the printed table matches the
checksum of ``data/processed/descriptors_subset.csv``.
"""

import subprocess
import sys

def test_verify_checksum():
    # Execute the verification script as a subprocess to capture its exit code.
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline.verify_checksum"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, (
        f"Checksum verification failed (exit {result.returncode}). "
        f"Stdout: {result.stdout.decode()}\nStderr: {result.stderr.decode()}"
    )