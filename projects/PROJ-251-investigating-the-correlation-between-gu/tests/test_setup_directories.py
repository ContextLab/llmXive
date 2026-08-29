import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the project root
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create the code directory to allow imports
        Path("code").mkdir()
        Path("code/__init__.py").touch()

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_directory_creation(self):
        """Test that all required directories are created."""
        result = create_directories()
        self.assertTrue(result)

        # Verify directories exist
        base_path = Path(self.temp_dir)
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_path} is not a directory")

    def test_contracts_directory_creation(self):
        """Test that the contracts directory is created."""
        create_directories()
        base_path = Path(self.temp_dir)
        contracts_path = base_path / "specs" / "001-investigating-the-correlation-between-gu" / "contracts"
        self.assertTrue(contracts_path.exists())
        self.assertTrue(contracts_path.is_dir())

    def test_idempotency(self):
        """Test that running create_directories twice does not cause errors."""
        result1 = create_directories()
        result2 = create_directories()
        self.assertTrue(result1)
        self.assertTrue(result2)

if __name__ == "__main__":
    unittest.main()