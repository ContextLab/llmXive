"""
Test that the quick‑start entry point can be executed via
``python -m src.main --config config.yaml`` without raising an exception.
"""

import subprocess
import sys
from pathlib import Path


def test_quickstart_runs_successfully(tmp_path: Path):
    """
    Run the module as a subprocess and assert a zero exit code.
    The test does not require the full pipeline to be implemented;
    it only verifies that the module can be imported and executed.
    """
    # Ensure we are invoking the interpreter from the project root.
    # The test runner's working directory is the project root.
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--config", "config.yaml"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"src.main exited with code {result.returncode}. "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )