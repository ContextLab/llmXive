import subprocess
import sys
from pathlib import Path

def test_run_all_help():
    """Verify that the orchestrator help command exits with status 0."""
    # Use sys.executable to ensure we use the same python environment
    result = subprocess.run(
        [sys.executable, "code/run_all.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Run the full brain‑network dynamics pipeline" in result.stdout

def test_run_all_invalid_arg():
    """Verify that invalid arguments cause a non-zero exit code."""
    result = subprocess.run(
        [sys.executable, "code/run_all.py", "--non-existent-flag"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0