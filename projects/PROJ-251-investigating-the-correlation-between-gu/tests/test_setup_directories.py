import unittest
import os
from pathlib import Path
import tempfile
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_create_directories_creates_all_required_dirs(self):
        """Test that all required directories are created."""
        create_directories(self.test_path)
        
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "data/research",
            "tests"
        ]
        
        for dir_name in expected_dirs:
            dir_path = self.test_path / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(dir_path.is_dir(), f"{dir_path} exists but is not a directory")
    
    def test_create_directories_handles_existing_dirs(self):
        """Test that existing directories don't cause errors."""
        # Create some directories beforehand
        (self.test_path / "code").mkdir()
        (self.test_path / "data").mkdir()
        (self.test_path / "data" / "raw").mkdir()
        
        # Should not raise
        create_directories(self.test_path)
        
        # Verify they still exist
        self.assertTrue((self.test_path / "code").exists())
        self.assertTrue((self.test_path / "data" / "raw").exists())
    
    def test_create_directories_creates_nested_dirs(self):
        """Test that nested directories are created correctly."""
        create_directories(self.test_path)
        
        # Check nested structure
        self.assertTrue((self.test_path / "data" / "raw").exists())
        self.assertTrue((self.test_path / "data" / "processed").exists())
        self.assertTrue((self.test_path / "data" / "results").exists())
        self.assertTrue((self.test_path / "data" / "research").exists())

if __name__ == "__main__":
    unittest.main()
