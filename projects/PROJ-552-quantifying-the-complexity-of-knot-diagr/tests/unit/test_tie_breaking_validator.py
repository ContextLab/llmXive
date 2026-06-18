"""Basic sanity test for the tie‑breaking validator script."""

import subprocess
import sys
from pathlib import Path

def test_tie_breaking_validator_runs():
    """The script should exit with code 0 and produce no traceback."""
    script = Path("code/reproducibility/tie_breaking_validator.py")
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, f"STDERR: {result.stderr}"