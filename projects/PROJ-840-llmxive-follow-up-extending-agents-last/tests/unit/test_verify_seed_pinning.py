"""
Unit test for the seed‑pinning compliance verifier (T004b).

The test simply runs the verifier script against the current repository.
Because the repository is expected to be compliant (the script was written
to satisfy FR‑008), the script should exit with status 0.
"""

import subprocess
import sys
from pathlib import Path

def test_seed_pinning_compliance():
    # Resolve the path to the verifier script relative to this test file
    script_path = (
        Path(__file__).resolve()
        .parents[2]  # go from tests/unit/ -> tests/ -> project root
        / "code"
        / "utils"
        / "verify_seed_pinning.py"
    )
    # Execute the script using the same Python interpreter that runs the tests
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    # The script should exit with code 0 (no violations)
    assert result.returncode == 0, (
        f"Seed‑pinning verifier reported violations:\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )