import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.test_dir = tempfile.mkdtemp()
        # Change to test directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a dummy code directory to simulate existing structure
        Path("code").mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_create_directories_structure(self):
        """Test that all required directories are created."""
        # Run the function
        created_paths = create_directories()
        
        # Verify all expected directories exist
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts"
        ]
        
        for dir_name in expected_dirs:
            full_path = Path(dir_name)
            self.assertTrue(full_path.exists(), f"Directory {dir_name} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_name} is not a directory")

    def test_create_directories_returns_paths(self):
        """Test that the function returns a list of paths."""
        created_paths = create_directories()
        self.assertIsInstance(created_paths, list)
        self.assertGreater(len(created_paths), 0)
        
        for path in created_paths:
            self.assertIsInstance(path, str)
            self.assertTrue(os.path.exists(path))

    def test_idempotency(self):
        """Test that running the function twice does not cause errors."""
        # First run
        paths1 = create_directories()
        
        # Second run
        paths2 = create_directories()
        
        # Should be the same directories
        self.assertEqual(len(paths1), len(paths2))
        self.assertEqual(set(paths1), set(paths2))

    def test_nested_directory_creation(self):
        """Test that nested directories (specs/.../contracts) are created correctly."""
        create_directories()
        
        contracts_path = Path("specs/001-investigating-the-correlation-between-gu/contracts")
        self.assertTrue(contracts_path.exists())
        self.assertTrue(contracts_path.is_dir())

if __name__ == '__main__':
    unittest.main()