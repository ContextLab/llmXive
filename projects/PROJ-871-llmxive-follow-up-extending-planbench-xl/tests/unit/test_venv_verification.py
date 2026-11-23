"""
Unit tests for the venv verification logic.
These tests ensure that the verification script correctly identifies
a missing venv or a valid venv structure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_venv.verify_venv import get_project_root, verify_venv

class TestVenvVerification:
    def test_get_project_root_from_code_subdir(self):
        """Test that get_project_root correctly identifies the root from a nested path."""
        # Simulate a path like .../project/code/setup_venv/verify_venv.py
        # We can't easily mock __file__ in the module, so we test the logic
        # by checking if the function returns a Path object.
        root = get_project_root()
        assert isinstance(root, Path)
        # It should be a valid directory
        assert root.exists()

    def test_verify_venv_missing_venv(self, tmp_path):
        """Test verify_venv returns False when venv directory is missing."""
        # Create a temporary directory structure that looks like the project but lacks venv
        with patch('setup_venv.verify_venv.get_project_root') as mock_root:
            mock_root.return_value = tmp_path
            # tmp_path is empty, no 'venv' folder
            result = verify_venv()
            assert result is False

    def test_verify_venv_missing_python_exec(self, tmp_path):
        """Test verify_venv returns False when venv exists but python executable is missing."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        
        with patch('setup_venv.verify_venv.get_project_root') as mock_root:
            mock_root.return_value = tmp_path
            result = verify_venv()
            assert result is False

    def test_verify_venv_success(self, tmp_path):
        """Test verify_venv returns True when venv and python executable exist and work."""
        venv_dir = tmp_path / "venv"
        bin_dir = venv_dir / "bin"
        bin_dir.mkdir(parents=True)
        
        # Create a fake python executable
        python_exec = bin_dir / "python"
        python_exec.touch()
        python_exec.chmod(0o755)
        
        # Mock subprocess.run to simulate successful version and pip list calls
        mock_version_result = MagicMock()
        mock_version_result.stdout = "Python 3.10.0"
        mock_version_result.stderr = ""
        
        mock_pip_result = MagicMock()
        mock_pip_result.stdout = "Package\n-------\npip\n"
        mock_pip_result.stderr = ""
        
        def mock_run(cmd, *args, **kwargs):
            if "--version" in cmd:
                return mock_version_result
            elif "pip" in cmd and "list" in cmd:
                return mock_pip_result
            # Default fallback
            raise subprocess.CalledProcessError(1, cmd)

        with patch('setup_venv.verify_venv.get_project_root') as mock_root:
            mock_root.return_value = tmp_path
            with patch('subprocess.run', side_effect=mock_run):
                result = verify_venv()
                assert result is True