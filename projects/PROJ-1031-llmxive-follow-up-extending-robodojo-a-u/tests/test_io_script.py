"""
Integration test for the updated IO utility.
Ensures that the script runs without error and that the streamed record
contains at least one field.
"""
import subprocess
import sys
import os

def test_io_script_runs():
    # Execute the shell wrapper which runs the module in both modes.
    script_path = os.path.join(os.path.dirname(__file__), "..", "code", "utils", "run_io_test.sh")
    result = subprocess.run([script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"IO script failed: {result.stderr}"
    # Basic sanity check on stdout.
    assert "IO script verification completed successfully." in result.stdout