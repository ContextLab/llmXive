"""Unit test for T001 verification script."""

import subprocess
import sys
from pathlib import Path

def test_verify_t001_success():
    """Run the verification script and expect a zero exit code."""
    script_path = Path(__file__).resolve().parents[2] / "code" / "verify_t001.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Verification failed: {result.stdout}\\n{result.stderr}"