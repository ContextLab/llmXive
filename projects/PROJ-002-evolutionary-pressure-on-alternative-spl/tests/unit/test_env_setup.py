"""
Unit tests for environment setup verification.
"""
import sys
import pytest
from pathlib import Path

def test_python_version_minimum():
    """Verify that the running Python version is at least 3.11."""
    version = sys.version_info
    assert version.major == 3, "Must be Python 3"
    assert version.minor >= 11, f"Python version must be >= 3.11, found {version.major}.{version.minor}"

def test_requirements_file_exists():
    """Verify that requirements.txt exists in the project root."""
    requirements_path = Path(__file__).parent.parent.parent / "requirements.txt"
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"

def test_r_requirements_file_exists():
    """Verify that requirements-r.txt exists in the project root."""
    r_requirements_path = Path(__file__).parent.parent.parent / "requirements-r.txt"
    assert r_requirements_path.exists(), f"requirements-r.txt not found at {r_requirements_path}"

def test_setup_python_script_exists():
    """Verify that setup_python_env.py exists."""
    setup_script = Path(__file__).parent.parent.parent / "code" / "setup_python_env.py"
    assert setup_script.exists(), f"setup_python_env.py not found at {setup_script}"

def test_setup_r_script_exists():
    """Verify that setup_r_env.R exists."""
    setup_script = Path(__file__).parent.parent.parent / "code" / "setup_r_env.R"
    assert setup_script.exists(), f"setup_r_env.R not found at {setup_script}"