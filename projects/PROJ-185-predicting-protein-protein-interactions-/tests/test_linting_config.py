import subprocess
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent

def test_ruff_check_passes(project_root):
    """Verify that ruff check passes on the codebase (ignoring E501)."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Ruff returns 0 if no errors, 1 if errors found
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes(project_root):
    """Verify that black check passes on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"