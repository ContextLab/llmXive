import pytest
import subprocess
import sys
from pathlib import Path

def test_pytest_discoverable():
    """Verify that pytest can discover and run a simple test."""
    project_root = Path(__file__).parent.parent.parent
    pytest_path = sys.executable
    result = subprocess.run(
        [pytest_path, "-m", "pytest", "--collect-only", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Pytest discovery failed: {result.stderr}"
    assert "collected" in result.stdout, "No tests were collected"
