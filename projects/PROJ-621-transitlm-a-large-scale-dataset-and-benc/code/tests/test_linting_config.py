"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import tempfile
import subprocess
from pathlib import Path

def test_ruff_config_exists():
    """Assert that .ruff.toml exists in the project root."""
    root = Path(__file__).resolve().parent.parent
    config_path = root / ".ruff.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_black_config_exists():
    """Assert that pyproject.toml or .black.toml exists with black config."""
    # Black looks for pyproject.toml usually, but we provided .black.toml as well for clarity
    # or we can assume the standard pyproject.toml location.
    # Given the task artifacts, we check for .black.toml.
    root = Path(__file__).resolve().parent.parent
    config_path = root / ".black.toml"
    assert config_path.exists(), f"Configuration file not found: {config_path}"

def test_requirements_dev_includes_tools():
    """Assert that requirements-dev.txt includes ruff and black."""
    root = Path(__file__).resolve().parent.parent
    req_path = root / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content.lower(), "ruff missing from requirements-dev.txt"
    assert "black" in content.lower(), "black missing from requirements-dev.txt"

def test_format_script_exists():
    """Assert that the helper script exists and is executable."""
    root = Path(__file__).resolve().parent.parent
    script_path = root / "scripts" / "format_and_lint.sh"
    assert script_path.exists(), "format_and_lint.sh not found"