import os
import subprocess
import sys
from pathlib import Path
import pytest

def test_flake8_config_exists():
    """Verify that .flake8 exists in the code directory."""
    flake8_path = Path("code/.flake8")
    assert flake8_path.exists(), "Missing code/.flake8"
    content = flake8_path.read_text()
    assert "max-line-length" in content, "max-line-length not configured in .flake8"

def test_pyproject_black_config_exists():
    """Verify that pyproject.toml exists and contains black configuration."""
    pyproject_path = Path("code/pyproject.toml")
    assert pyproject_path.exists(), "Missing code/pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length = 88" in content, "line-length not set to 88 in pyproject.toml"

def test_black_check_passes():
    """Run black --check on the code directory to ensure formatting compliance."""
    # We run black from the project root, targeting the code/ directory
    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=Path(".").resolve(),
        capture_output=True,
        text=True
    )
    # Exit code 0 means all files are formatted correctly
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_flake8_check_passes():
    """Run flake8 on the code directory to ensure linting compliance."""
    result = subprocess.run(
        ["flake8", "code/"],
        cwd=Path(".").resolve(),
        capture_output=True,
        text=True
    )
    # Exit code 0 means no linting errors found
    # Note: We ignore specific errors in .flake8 config, so this should pass
    assert result.returncode == 0, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"