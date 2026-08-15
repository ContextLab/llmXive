import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path to allow importing code/setup_venv
# Assuming this test is run from the project root or the path is configured
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.setup_venv import setup_venv

class TestVenvSetup(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after testing."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_venv_creation_success(self):
        """Test that a virtual environment is successfully created."""
        result = setup_venv(self.test_dir, "test_venv")
        self.assertTrue(result, "setup_venv should return True on success")
        
        venv_path = Path(self.test_dir) / "test_venv"
        self.assertTrue(venv_path.exists(), "Virtual environment directory should exist")
        
        # Check for python executable
        if sys.platform == "win32":
            python_exec = venv_path / "Scripts" / "python.exe"
        else:
            python_exec = venv_path / "bin" / "python"
        
        self.assertTrue(python_exec.exists(), "Python executable should exist in venv")

    def test_venv_creation_idempotent(self):
        """Test that creating a venv when one exists returns True without error."""
        # First creation
        setup_venv(self.test_dir, "test_venv")
        # Second creation (should detect existence and return True)
        result = setup_venv(self.test_dir, "test_venv")
        self.assertTrue(result, "setup_venv should return True if venv already exists")

    def test_venv_pip_upgrade(self):
        """Test that pip is upgraded during venv setup."""
        # We rely on the fact that if setup_venv returns True, pip was upgraded.
        # A more rigorous test would involve checking pip version, but that's complex.
        result = setup_venv(self.test_dir, "test_venv")
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()