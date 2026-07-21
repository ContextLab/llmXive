import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent

def test_black_config_valid(project_root):
    """Test that black configuration is valid and can parse pyproject.toml"""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30
    )
    # We expect this to fail if code isn't formatted, but the config must be valid
    # The exit code 1 means "would reformat", 0 means "all good", other codes mean errors
    # We only care that the config didn't crash black
    assert result.returncode in [0, 1], f"Black failed with config error: {result.stderr}"

def test_ruff_config_valid(project_root):
    """Test that ruff configuration is valid and can parse pyproject.toml"""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format=json", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30
    )
    # Ruff should run without configuration errors
    # Exit code 0: no issues, 1: issues found, 2: configuration error
    assert result.returncode != 2, f"Ruff configuration error: {result.stderr}"