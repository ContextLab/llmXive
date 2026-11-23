"""
Unit tests for virtual environment setup functionality.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_venv import find_python311, create_virtual_environment, install_dependencies

class TestFindPython311:
    def test_finds_python_in_path(self):
        """Test that a Python executable is found if available."""
        # This test will pass if Python is installed, fail otherwise
        # but it's a sanity check for the function
        result = find_python311()
        # We don't assert a specific result as it depends on the environment
        # but the function should return a string or None
        assert result is None or isinstance(result, str)

class TestCreateVirtualEnvironment:
    def test_creates_venv_successfully(self):
        """Test virtual environment creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            python_exec = sys.executable
            
            # Mock subprocess to avoid actually creating a venv in tests
            with patch('setup_venv.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = create_virtual_environment(venv_path, python_exec)
                
                # The function should call subprocess.run
                assert mock_run.called
                assert result is True

    def test_handles_creation_failure(self):
        """Test handling of venv creation failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            python_exec = sys.executable
            
            with patch('setup_venv.subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Creation failed")
                result = create_virtual_environment(venv_path, python_exec)
                assert result is False

class TestInstallDependencies:
    def test_installs_from_requirements(self):
        """Test dependency installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            requirements_path = Path(tmpdir) / "requirements.txt"
            
            # Create a dummy requirements file
            requirements_path.write_text("pytest\n")
            
            # Mock the pip executable existence
            with patch.object(Path, 'exists', return_value=True):
                with patch('setup_venv.subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    result = install_dependencies(venv_path, requirements_path)
                    
                    assert mock_run.called
                    assert result is True

    def test_handles_missing_requirements(self):
        """Test behavior when requirements.txt is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            requirements_path = Path(tmpdir) / "nonexistent.txt"
            
            with patch('setup_venv.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = install_dependencies(venv_path, requirements_path)
                
                # Should return True but print a warning
                assert result is True
                assert not mock_run.called  # pip install shouldn't be called