import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to allow importing setup_venv
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_venv import setup_venv

class TestVenvSetup(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_venv_creation(self):
        """Test that setup_venv creates a valid virtual environment."""
        result = setup_venv(self.project_root)
        
        self.assertTrue(result, "setup_venv should return True on success")
        
        venv_dir = self.project_root / "venv"
        self.assertTrue(venv_dir.exists(), "venv directory should exist")
        
        # Check for standard venv structure
        if sys.platform != "win32":
            self.assertTrue((venv_dir / "bin" / "python").exists(), "python executable should exist")
            self.assertTrue((venv_dir / "bin" / "pip").exists(), "pip executable should exist")
        else:
            self.assertTrue((venv_dir / "Scripts" / "python.exe").exists(), "python.exe should exist")
            self.assertTrue((venv_dir / "Scripts" / "pip.exe").exists(), "pip.exe should exist")

    def test_venv_idempotency(self):
        """Test that running setup_venv twice does not fail."""
        # First run
        result1 = setup_venv(self.project_root)
        self.assertTrue(result1)
        
        # Second run (should detect existing venv and return True)
        result2 = setup_venv(self.project_root)
        self.assertTrue(result2)

    def test_venv_missing_activate_fails(self):
        """Test that setup_venv returns False if bin/activate is missing in an existing dir."""
        # Create the directory manually but without the activate script
        self.venv_path.mkdir(parents=True)
        
        result = setup_venv(self.project_root)
        
        self.assertFalse(result, "setup_venv should return False if activate script is missing")

if __name__ == '__main__':
    unittest.main()