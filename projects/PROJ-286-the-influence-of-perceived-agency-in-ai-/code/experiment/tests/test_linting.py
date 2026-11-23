import subprocess
import sys
import pytest
from pathlib import Path

@pytest.mark.linting
def test_black_check():
    """Verify that black formatting check passes on the project."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # Exit code 0 means formatting is correct
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

@pytest.mark.linting
def test_flake8_check():
    """Verify that flake8 linting check passes on the project."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "flake8"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    # Exit code 0 means no linting errors
    assert result.returncode == 0, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
