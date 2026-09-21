import subprocess
import os
from pathlib import Path

def test_ruff_exists():
    """Verify ruff is installed."""
    result = subprocess.run(["ruff", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Ruff is not installed or not in PATH"

def test_black_exists():
    """Verify black is installed."""
    result = subprocess.run(["black", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Black is not installed or not in PATH"