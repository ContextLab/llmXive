import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate project root."""
        self.test_dir = tempfile.mkdtemp()
        # Change to test dir to simulate running from project root
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a fake code/ directory to simulate existing structure if needed
        # but we want to test creation, so we ensure they don't exist initially
        # by using the temp dir which is empty
        
    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_create_directories_creates_all_paths(self):
        """Test that create_directories creates all required paths."""
        # Run the function
        result = create_directories()
        
        self.assertTrue(result)
        
        # Verify directories exist
        base_path = Path(self.test_dir)
        
        expected_dirs = [
            base_path / "code",
            base_path / "data" / "raw",
            base_path / "data" / "processed",
            base_path / "data" / "results",
            base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        ]
        
        for dir_path in expected_dirs:
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(dir_path.is_dir(), f"{dir_path} is not a directory")

    def test_create_directories_idempotent(self):
        """Test that running create_directories twice doesn't cause errors."""
        # Run twice
        result1 = create_directories()
        result2 = create_directories()
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        
        # Verify all directories still exist
        base_path = Path(self.test_dir)
        expected_dirs = [
            base_path / "code",
            base_path / "data" / "raw",
            base_path / "data" / "processed",
            base_path / "data" / "results",
            base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        ]
        
        for dir_path in expected_dirs:
            self.assertTrue(dir_path.exists())
            
    def test_contract_directory_exists(self):
        """Specific test for the contracts directory requirement."""
        create_directories()
        
        base_path = Path(self.test_dir)
        contracts_path = base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        
        self.assertTrue(contracts_path.exists())
        self.assertTrue(contracts_path.is_dir())
        # Verify it's a directory (not empty check, just existence)
        self.assertTrue(contracts_path.is_dir())

if __name__ == "__main__":
    unittest.main()