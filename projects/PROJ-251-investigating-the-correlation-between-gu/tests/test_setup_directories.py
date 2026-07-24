import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import the module under test
# Since setup_directories.py is in code/, we need to adjust sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories


class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to simulate project root."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_creates_all_required_directories(self):
        """Test that all required directories are created."""
        result = create_directories()
        
        self.assertTrue(result)
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts"
        ]
        
        for dir_name in required_dirs:
            full_path = Path(self.test_dir) / dir_name
            self.assertTrue(full_path.exists(), f"Directory {dir_name} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_name} exists but is not a directory")

    def test_handles_existing_directories_gracefully(self):
        """Test that the function doesn't fail if directories already exist."""
        # Pre-create some directories
        Path(self.test_dir, "code").mkdir()
        Path(self.test_dir, "data").mkdir()
        Path(self.test_dir, "data", "raw").mkdir()
        
        # Should not raise an exception
        result = create_directories()
        
        self.assertTrue(result)

    def test_fails_on_file_collision(self):
        """Test that the function raises an error if a path exists but is not a directory."""
        # Create a file where a directory is expected
        code_path = Path(self.test_dir, "code")
        code_path.touch()  # Create a file instead of directory
        
        with self.assertRaises(FileExistsError):
            create_directories()

    def test_creates_nested_directories(self):
        """Test that nested directories (like specs/.../contracts) are created."""
        result = create_directories()
        
        self.assertTrue(result)
        
        # Check the deepest nested directory
        contracts_path = Path(self.test_dir) / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        self.assertTrue(contracts_path.exists())
        self.assertTrue(contracts_path.is_dir())


if __name__ == "__main__":
    unittest.main()