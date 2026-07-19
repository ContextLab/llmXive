import os
import unittest
import tempfile
import shutil
from pathlib import Path

# Adjust import path to match project structure
# Assuming this test is run from project root or code/tests
try:
    from code.setup_directories import create_directories
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from setup_directories import create_directories
    import sys

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate project root."""
        self.test_root = tempfile.mkdtemp()
        # Save original cwd
        self.original_cwd = os.getcwd()
        # Change to test root to simulate project environment
        os.chdir(self.test_root)
        
        # Create a dummy code/ directory structure to make setup_directories.py importable
        # if the script relies on its own location relative to the root
        os.makedirs(os.path.join(self.test_root, "code"), exist_ok=True)
        # Copy the script to the test location if needed, or rely on sys.path
        
    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        # Run the function
        result = create_directories()
        
        self.assertTrue(result["success"], f"Errors occurred: {result['errors']}")
        self.assertIn("code", result["created"][0]) # Check first one exists
        
        # Verify specific paths exist on disk
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts"
        ]
        
        for rel_dir in expected_dirs:
            full_path = Path(self.test_root) / rel_dir
            self.assertTrue(full_path.exists(), f"Directory {full_path} was not created.")
            self.assertTrue(full_path.is_dir(), f"{full_path} is not a directory.")

    def test_handles_existing_directories(self):
        """Verify function handles pre-existing directories gracefully."""
        # Pre-create one directory
        pre_existing = Path(self.test_root) / "data" / "raw"
        pre_existing.mkdir(parents=True, exist_ok=True)
        
        # Run the function
        result = create_directories()
        
        self.assertTrue(result["success"])
        # Should report success even if some already existed

    def test_nested_contract_directory(self):
        """Verify deep nested directory creation for specs."""
        result = create_directories()
        self.assertTrue(result["success"])
        
        contract_path = Path(self.test_root) / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        self.assertTrue(contract_path.exists())
        self.assertTrue(contract_path.is_dir())

if __name__ == "__main__":
    unittest.main()