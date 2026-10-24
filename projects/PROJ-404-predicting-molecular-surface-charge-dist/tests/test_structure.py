"""
Unit test that imports the `setup_structure` script and checks that it runs without
raising an exception. This test is optional but provides CI‑level assurance that the
directory creation logic works on a clean checkout.
"""
import subprocess
import sys
import pathlib

def test_setup_structure_runs():
    """Execute the setup script and expect a zero exit code."""
    script_path = pathlib.Path(__file__).resolve().parents[2] / "code" / "setup_structure.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"