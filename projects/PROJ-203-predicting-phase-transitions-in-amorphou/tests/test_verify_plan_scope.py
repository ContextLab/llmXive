"""Unit test for the plan scope verification script."""

import subprocess
import sys
from pathlib import Path

def test_verify_plan_scope_script():
    """
    Execute the verification script and assert it exits with code 0.
    The script itself prints a helpful message on success.
    """
    script_path = Path(__file__).parents[2] / "code" / "verify_plan_scope.py"
    # Run the script using the same Python interpreter
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    # The script should exit with status 0
    assert result.returncode == 0, (
        f"Script exited with non‑zero status {result.returncode}. "
        f"Stderr: {result.stderr}"
    )
    # Optionally check the success message
    assert "Verification passed" in result.stdout