import subprocess
import pytest
from pathlib import Path

def test_black_check():
    """Test that black check passes on code directory."""
    result = subprocess.run(
        ["black", "--check", "code/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_flake8_check():
    """Test that flake8 check passes on code directory."""
    result = subprocess.run(
        ["flake8", "code/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
