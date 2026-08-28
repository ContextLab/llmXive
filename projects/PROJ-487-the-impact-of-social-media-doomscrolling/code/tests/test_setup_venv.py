import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

from setup_venv import setup_venv

class TestVenvSetup(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_venv_success(self):
        """Test that a virtual environment is created successfully."""
        result = setup_venv(self.project_root)
        venv_path = self.project_root / "venv"
        
        self.assertTrue(result)
        self.assertTrue(venv_path.exists())
        
        # Check for activation script (Unix)
        activate_script = venv_path / "bin" / "activate"
        # Check for activation script (Windows)
        activate_script_win = venv_path / "Scripts" / "activate.bat"
        
        self.assertTrue(activate_script.exists() or activate_script_win.exists())

    def test_create_venv_already_exists(self):
        """Test that setup returns True if venv already exists."""
        # Create the venv directory first
        venv_path = self.project_root / "venv"
        venv_path.mkdir(parents=True)
        
        result = setup_venv(self.project_root)
        
        # Should return True since it already exists
        self.assertTrue(result)

    def test_create_venv_pip_installed(self):
        """Test that pip is installed in the new virtual environment."""
        result = setup_venv(self.project_root)
        self.assertTrue(result)
        
        venv_path = self.project_root / "venv"
        pip_path = venv_path / "bin" / "pip"
        pip_path_win = venv_path / "Scripts" / "pip.exe"
        
        # At least one should exist
        self.assertTrue(pip_path.exists() or pip_path_win.exists())

if __name__ == "__main__":
    unittest.main()