import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil
import subprocess

# Add the code directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_env import ensure_virtual_environment, install_dependencies


class TestVirtualEnvironmentSetup:
    """Tests for virtual environment creation and dependency installation."""

    def test_ensure_virtual_environment_creates_new_venv(self):
        """Test that a new virtual environment is created when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            
            # Verify venv doesn't exist yet
            assert not venv_path.exists()
            
            # Create it
            result = ensure_virtual_environment(str(venv_path))
            
            # Verify it was created
            assert result is True
            assert venv_path.exists()
            assert (venv_path / "pyvenv.cfg").exists()
            
            # Verify basic structure exists
            if os.name == "nt":
                assert (venv_path / "Scripts").exists()
                assert (venv_path / "Scripts" / "python.exe").exists()
            else:
                assert (venv_path / "bin").exists()
                assert (venv_path / "bin" / "python").exists()

    def test_ensure_virtual_environment_existing_venv(self):
        """Test that existing virtual environment is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "existing_venv"
            
            # Create a fake venv structure
            venv_path.mkdir()
            (venv_path / "pyvenv.cfg").write_text("home = /usr/bin")
            
            # Should return True without error
            result = ensure_virtual_environment(str(venv_path))
            assert result is True

    def test_install_dependencies_missing_requirements(self):
        """Test that installation fails gracefully when requirements.txt is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            requirements_path = Path(tmpdir) / "nonexistent.txt"
            
            # Create a venv first
            ensure_virtual_environment(str(venv_path))
            
            # Try to install from missing file
            result = install_dependencies(str(requirements_path), str(venv_path))
            
            assert result is False

    def test_install_dependencies_with_empty_requirements(self):
        """Test that installation succeeds with an empty requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            requirements_path = Path(tmpdir) / "requirements.txt"
            
            # Create venv
            ensure_virtual_environment(str(venv_path))
            
            # Create empty requirements file
            requirements_path.write_text("")
            
            # Should succeed (no packages to install)
            result = install_dependencies(str(requirements_path), str(venv_path))
            assert result is True

    def test_install_dependencies_with_valid_requirements(self):
        """Test installation with a minimal valid requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            requirements_path = Path(tmpdir) / "requirements.txt"
            
            # Create venv
            ensure_virtual_environment(str(venv_path))
            
            # Create requirements with a small, quick-to-install package
            requirements_path.write_text("six>=1.0.0\n")
            
            # Should succeed
            result = install_dependencies(str(requirements_path), str(venv_path))
            assert result is True

    def test_install_dependencies_without_venv(self):
        """Test that installation fails when venv doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_path = Path(tmpdir) / "requirements.txt"
            venv_path = Path(tmpdir) / "nonexistent_venv"
            
            # Create requirements file
            requirements_path.write_text("six>=1.0.0\n")
            
            # Should fail because venv doesn't exist
            result = install_dependencies(str(requirements_path), str(venv_path))
            assert result is False
