"""
Unit test for the T001 verification script (code/verify_t001.py).

The test simply imports the verification module and runs its ``main``
function, asserting that the exit code is ``0``.  This ensures that the
skeleton creation script correctly creates all required directories and
the per‑sample schema with the ``abs_error`` column.
"""

import subprocess
import sys
from pathlib import Path

def test_verify_t001_exit_code():
    """
    Execute ``python -m code.verify_t001`` and check that it exits with 0.
    """
    # Resolve the module path relative to the project root.
    module_path = Path(__file__).resolve().parents[2] / "code" / "verify_t001.py"
    result = subprocess.run(
        [sys.executable, str(module_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Verification script failed with code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )