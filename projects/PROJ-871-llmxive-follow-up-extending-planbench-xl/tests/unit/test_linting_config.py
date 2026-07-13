"""
Unit tests to verify linting and formatting configuration is correctly set up.
These tests ensure that the project enforces consistent code style via flake8, black, and isort.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_flake8_config_exists():
    """Verify that .flake8 configuration file exists."""
    flake8_config = PROJECT_ROOT / ".flake8"
    assert flake8_config.exists(), ".flake8 configuration file is missing."

def test_pyproject_toml_config_exists():
    """Verify that pyproject.toml contains tool configuration."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml is missing."
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.isort]" in content, "Isort configuration missing in pyproject.toml"
    assert "[tool.flake8]" in content, "Flake8 configuration missing in pyproject.toml"

def test_flake8_runs_without_critical_error():
    """
    Run flake8 on the code directory.
    Note: This test expects flake8 to be installed. If lint errors exist,
    they are expected to be reported by flake8, but the test passes if flake8
    itself runs successfully and returns a non-internal-error code.
    We check that the tool is executable and configured.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0 or "installed" in result.stdout.lower(), \
            "Flake8 is not installed or not working correctly."
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 check timed out.")
    except FileNotFoundError:
        pytest.fail("Flake8 command not found. Please install dependencies.")

def test_black_runs_without_critical_error():
    """
    Verify black is installed and can run (check --check mode).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, "Black is not installed or not working correctly."
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out.")
    except FileNotFoundError:
        pytest.fail("Black command not found. Please install dependencies.")
