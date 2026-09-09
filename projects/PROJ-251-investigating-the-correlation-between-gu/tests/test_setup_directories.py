import unittest
import os
from pathlib import Path
import tempfile
import shutil
import sys

# Add the project root to the path so we can import code.setup_directories
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.base_path = Path(self.test_dir)
    
    def tearDown(self):
        """Remove the temporary directory after testing."""
        shutil.rmtree(self.test_dir)
    
    def test_directories_created(self):
        """Test that all required directories are created."""
        create_directories(self.base_path)
        
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "data/research",
            "tests",
        ]
        
        for dir_path in expected_dirs:
            full_path = self.base_path / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_path} exists but is not a directory")
    
    def test_idempotent_creation(self):
        """Test that running create_directories twice doesn't cause errors."""
        create_directories(self.base_path)
        create_directories(self.base_path)  # Should not raise
        
        # Verify directories still exist
        expected_dirs = ["code", "data/raw", "data/processed", "data/results", "data/research", "tests"]
        for dir_path in expected_dirs:
            self.assertTrue((self.base_path / dir_path).exists())

if __name__ == '__main__':
    unittest.main()