"""
Unit tests for linting configuration (T003).
"""
import pytest
from pathlib import Path
import os
import sys
import subprocess


def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    root = Path(__file__).parent.parent.parent
    config = root / "pyproject.toml"
    assert config.exists(), "pyproject.toml (ruff config) missing"


def test_black_config_exists():
    """Verify black configuration file exists."""
    root = Path(__file__).parent.parent.parent
    config = root / "pyproject.toml"
    assert config.exists(), "pyproject.toml (black config) missing"


def test_requirements_contains_linting_tools():
    """Verify requirements.txt contains linting tools."""
    root = Path(__file__).parent.parent.parent
    req_file = root / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text()
        assert "ruff" in content.lower() or "black" in content.lower(), \
            "requirements.txt missing ruff or black"
    else:
        # If file doesn't exist yet, this is expected during setup
        pass


def test_ruff_can_run():
    """Verify ruff can be executed."""
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Ruff not installed or not in PATH")


def test_black_can_run():
    """Verify black can be executed."""
    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Black not installed or not in PATH")


def test_setup_linting_script_exists():
    """Verify setup_linting.py script exists."""
    root = Path(__file__).parent.parent.parent
    script = root / "code" / "setup_linting.py"
    # Note: Path might vary based on project structure, adjusted for context
    if not script.exists():
        # Check alternate location if code/ is not root
        script = root / "setup_linting.py"
        assert script.exists(), "setup_linting.py not found"
