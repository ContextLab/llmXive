"""
Smoke test to verify that linting tools are installed and configured.
This test ensures the development environment for T003 is valid.
"""
import subprocess
import sys

def test_flake8_installed():
    """Verify flake8 is importable/available."""
    try:
        import flake8
    except ImportError:
        # Try subprocess to see if it's in PATH
        result = subprocess.run(
            ["flake8", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "flake8 not found in PATH"

def test_black_installed():
    """Verify black is importable/available."""
    try:
        import black
    except ImportError:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "black not found in PATH"

def test_isort_installed():
    """Verify isort is importable/available."""
    try:
        import isort
    except ImportError:
        result = subprocess.run(
            ["isort", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "isort not found in PATH"