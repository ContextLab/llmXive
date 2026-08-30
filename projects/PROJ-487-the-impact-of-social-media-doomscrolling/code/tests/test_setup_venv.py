import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to allow imports
# Assuming this test is run from code/tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_venv import setup_venv

class TestVenvSetup(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.venv_path = self.project_root / "venv"

    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_venv_creation(self):
        """Test that setup_venv creates the virtual environment directory."""
        self.assertFalse(self.venv_path.exists(), "Venv should not exist before test")
        
        result = setup_venv(self.project_root)
        
        self.assertTrue(result, "setup_venv should return True on success")
        self.assertTrue(self.venv_path.exists(), "Virtual environment directory should exist")
        
        # Check for bin/activate
        activate_script = self.venv_path / "bin" / "activate"
        self.assertTrue(activate_script.exists(), "bin/activate script should exist")

    def test_venv_skips_existing(self):
        """Test that setup_venv returns True if venv already exists."""
        # Create the venv manually first
        import venv
        venv.create(self.venv_path, with_pip=True)
        
        result = setup_venv(self.project_root)
        
        self.assertTrue(result, "setup_venv should return True if venv exists")
        
        # Verify it wasn't recreated (still just one dir)
        self.assertTrue(self.venv_path.exists())

    def test_venv_missing_activate_fails(self):
        """Test that setup_venv returns False if bin/activate is missing in an existing dir."""
        # Create the directory manually but without the activate script
        self.venv_path.mkdir(parents=True)
        
        result = setup_venv(self.project_root)
        
        self.assertFalse(result, "setup_venv should return False if activate script is missing")

if __name__ == '__main__':
    unittest.main()