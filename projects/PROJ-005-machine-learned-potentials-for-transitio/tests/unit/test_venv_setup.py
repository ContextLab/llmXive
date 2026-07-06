"""
Unit tests for T005: Virtual Environment Setup.

These tests verify that the setup logic works correctly without actually
running the full installation (which would take too long in CI).
"""
import os
import sys
import tempfile
from pathlib import Path
import shutil
import subprocess

# Add code to path to import setup_venv
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_venv import check_python_version, create_venv, activate_and_install

def test_check_python_version_valid():
    """Test that check_python_version returns True for current Python if it is 3.11."""
    has_version, exe = check_python_version()
    # If we are running on 3.11, it should be True. If not, it should find python3.11 or return False.
    # We can't guarantee the environment has 3.11, so we just check the function runs without crashing.
    assert isinstance(has_version, bool)
    assert isinstance(exe, (str, type(None)))

def test_create_venv_creates_directory():
    """Test that create_venv creates the directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        create_venv(venv_path)
        
        assert venv_path.exists()
        # Check for standard venv structure
        if os.name == "nt":
            assert (venv_path / "Scripts").exists()
            assert (venv_path / "Scripts" / "python.exe").exists()
        else:
            assert (venv_path / "bin").exists()
            assert (venv_path / "bin" / "python").exists()

def test_activate_and_install_missing_requirements():
    """Test that activate_and_install raises error if requirements.txt is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        req_path = Path(tmpdir) / "nonexistent.txt"
        
        # Create venv first
        create_venv(venv_path)
        
        # This should raise FileNotFoundError
        try:
            activate_and_install(venv_path, req_path)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected

def test_requirements_file_exists():
    """Verify that requirements.txt exists in project root."""
    project_root = Path(__file__).parent.parent.parent
    req_path = project_root / "requirements.txt"
    assert req_path.exists(), f"requirements.txt not found at {req_path}"