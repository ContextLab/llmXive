"""
Unit tests for the virtual environment verification utility.
"""
import os
import sys
import tempfile
import stat
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.verify_venv import verify_venv


class TestVenvVerification(unittest.TestCase):
    """Tests for the verify_venv function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.venv_bin = self.test_dir / "venv" / "bin"
        self.venv_bin.mkdir(parents=True)
        self.activate_script = self.venv_bin / "activate"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_venv_activate_missing(self):
        """Test verification fails when activate script is missing."""
        result = verify_venv(self.test_dir)
        self.assertFalse(result)

    def test_venv_activate_not_executable(self):
        """Test verification fails when activate script is not executable."""
        self.activate_script.touch()
        # Ensure it's not executable
        os.chmod(self.activate_script, 0o644)

        result = verify_venv(self.test_dir)
        self.assertFalse(result)

    def test_venv_activate_executable(self):
        """Test verification passes when activate script exists and is executable."""
        self.activate_script.touch()
        # Make executable
        os.chmod(self.activate_script, 0o755)

        result = verify_venv(self.test_dir)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()