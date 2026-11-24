"""
Integration test for the seed‑pinning compliance checker.

The test simply runs the ``verify_seed_pinning.py`` script on the current
repository and asserts that it exits with status 0 (i.e. no violations).
"""

import subprocess
import sys
from pathlib import Path

def test_verify_seed_pinning_exit_code():
    """
    Execute the compliance script and ensure it reports no violations.
    """
    script_path = Path("code/utils/verify_seed_pinning.py")
    # Run the script with the project root as the scanning base.
    result = subprocess.run(
        [sys.executable, str(script_path), "--root", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # The script should exit with code 0 and print a success message.
    assert result.returncode == 0, (
        f"Script exited with {result.returncode}. "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )
    assert "No seed‑pinning violations found." in result.stdout