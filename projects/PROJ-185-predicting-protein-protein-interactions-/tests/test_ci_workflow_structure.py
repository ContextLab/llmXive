"""Test that the CI workflow structure validator runs without error."""

import subprocess
import sys
from pathlib import Path

def test_ci_workflow_structure():
    """Execute the validator script and assert a zero exit code."""
    # Resolve the script relative to the repository root
    script_path = Path(__file__).resolve().parents[2] / "code" / "ci" / "validate_workflow.py"

    # Run the script in a subprocess to capture its exit status
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The validator should exit with status 0 for a correctly‑structured workflow.
    assert result.returncode == 0, (
        f"Validator exited with {result.returncode}. "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )