"""
Tests for the virtual environment setup script.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_venv import setup_venv

class TestVenvSetup(unittest.TestCase):
    """Test cases for virtual environment setup functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('setup_venv.venv.create')
    @patch('setup_venv.subprocess.run')
    def test_create_venv_success(self, mock_subprocess, mock_venv_create):
        """Test successful creation of virtual environment."""
        mock_venv_create.return_value = None
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = setup_venv(self.project_root)

        self.assertTrue(result)
        mock_venv_create.assert_called_once_with(self.project_root / "venv", with_pip=True)
        mock_subprocess.assert_called()

    def test_venv_already_exists(self):
        """Test behavior when venv already exists."""
        # Create a fake venv structure
        venv_path = self.project_root / "venv"
        bin_dir = venv_path / "bin" if os.name != 'nt' else venv_path / "Scripts"
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create activate script
        activate_script = bin_dir / "activate"
        activate_script.touch()

        result = setup_venv(self.project_root)

        self.assertTrue(result)
        self.assertTrue(venv_path.exists())

    @patch('setup_venv.venv.create')
    def test_create_venv_failure(self, mock_venv_create):
        """Test behavior when venv creation fails."""
        mock_venv_create.side_effect = Exception("Creation failed")

        result = setup_venv(self.project_root)

        self.assertFalse(result)

    def test_project_root_does_not_exist(self):
        """Test behavior when project root doesn't exist."""
        non_existent_root = Path("/non/existent/path")

        # This should not raise an exception in setup_venv itself,
        # but the caller should handle it. We test the function directly.
        # In practice, the main() function would check this.
        result = setup_venv(non_existent_root)
        
        # The function should handle non-existent paths gracefully
        # or the caller should validate first
        # For this test, we expect it to return False or handle appropriately
        # Since venv.create will fail on non-existent parent, we expect False
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()