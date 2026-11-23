"""
Unit tests to verify linting and formatting configuration.
These tests ensure that ruff and black configurations are valid and
that the project structure adheres to the defined standards.
"""
import subprocess
import os
from pathlib import Path

def test_ruff_config_exists():
    """Verify that .ruff.toml exists in the code directory."""
    ruff_config = Path("code/.ruff.toml")
    assert ruff_config.exists(), ".ruff.toml configuration file is missing."

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains black/ruff config."""
    pyproject = Path("code/pyproject.toml")
    assert pyproject.exists(), "pyproject.toml is missing."
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml."
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml."

def test_ruff_check_passes():
    """Run ruff check on the code directory to ensure no linting errors."""
    # We check if ruff is available; if not, we skip (env dependent)
    try:
        result = subprocess.run(
            ["ruff", "check", "code/"],
            capture_output=True,
            text=True,
            timeout=60
        )
        # If ruff is not installed, we don't fail the test, just warn
        if result.returncode == 127:
            print("Warning: 'ruff' command not found. Skipping lint check.")
            return
        
        # If there are linting errors, the test fails
        assert result.returncode == 0, f"Ruff found linting errors:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        print("Warning: 'ruff' not installed. Skipping lint check.")

def test_black_check_passes():
    """Run black check on the code directory to ensure formatting compliance."""
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 127:
            print("Warning: 'black' command not found. Skipping format check.")
            return
        
        assert result.returncode == 0, f"Black found formatting issues:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        print("Warning: 'black' not installed. Skipping format check.")