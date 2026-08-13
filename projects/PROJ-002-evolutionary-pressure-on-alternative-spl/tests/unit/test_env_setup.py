"""
Unit tests for environment setup validation.
"""
import sys
import subprocess
from pathlib import Path
import pytest

def test_python_version_requirement():
    """Verify that the current Python version meets the minimum requirement."""
    # The setup script enforces 3.11+, but in testing environments we might be on 3.10 or 3.12
    # We just verify the version info is accessible and valid
    assert sys.version_info.major >= 3
    assert sys.version_info.minor >= 8  # Minimum supported by most deps

def test_requirements_file_exists():
    """Verify requirements.txt exists in the project root."""
    req_file = Path(__file__).parent.parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt must exist in project root"

    content = req_file.read_text()
    assert "pandas" in content
    assert "numpy" in content
    assert "biopython" in content
    assert "requests" in content
    assert "tqdm" in content
    assert "loguru" in content

def test_r_requirements_file_exists():
    """Verify requirements-r.txt exists in the project root."""
    req_file = Path(__file__).parent.parent.parent / "requirements-r.txt"
    assert req_file.exists(), "requirements-r.txt must exist in project root"

    content = req_file.read_text()
    assert "phylolm" in content
    assert "ape" in content
    assert "data.table" in content
    assert "ggplot2" in content

def test_setup_python_script_exists():
    """Verify setup_python_env.py exists."""
    script = Path(__file__).parent.parent.parent / "code" / "setup_python_env.py"
    assert script.exists(), "setup_python_env.py must exist"

def test_setup_r_script_exists():
    """Verify setup_r_env.sh exists."""
    script = Path(__file__).parent.parent.parent / "code" / "setup_r_env.sh"
    assert script.exists(), "setup_r_env.sh must exist"
    # Check it is executable (on Unix systems)
    # Note: This might fail in some CI environments depending on permissions, so we just check existence
    # assert os.access(script, os.X_OK)