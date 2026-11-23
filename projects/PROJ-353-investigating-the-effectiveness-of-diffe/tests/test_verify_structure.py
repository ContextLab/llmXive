"""
Integration test for the verify_structure script.

The test runs the verification module as a subprocess and asserts that it
exits with return code 0, indicating that all required directories are
present.
"""
import subprocess
import sys
from pathlib import Path

def test_verify_structure():
    # Run the verification script as a module.
    result = subprocess.run(
        [sys.executable, "-m", "code.verify_structure"],
        capture_output=True,
        text=True,
    )
    assert (
        result.returncode == 0
    ), f"Verification script failed (exit {result.returncode}).\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}"
