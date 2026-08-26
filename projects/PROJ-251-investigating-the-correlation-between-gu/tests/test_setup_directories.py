import unittest
import os
from pathlib import Path
import tempfile
import shutil
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate project root
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        # Restore original cwd and remove temp directory
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_directories_structure(self):
        """Test that all required directories are created."""
        create_directories()

        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "data/research",
            "specs/001-investigating-the-correlation-between-gu/contracts",
        ]

        for dir_name in required_dirs:
            full_path = Path(self.temp_dir) / dir_name
            self.assertTrue(
                full_path.exists(), 
                f"Directory {dir_name} was not created."
            )
            self.assertTrue(
                full_path.is_dir(), 
                f"{dir_name} exists but is not a directory."
            )

    def test_idempotency(self):
        """Test that running create_directories twice doesn't fail."""
        create_directories()
        # Should not raise an exception
        create_directories()

        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "data/research",
            "specs/001-investigating-the-correlation-between-gu/contracts",
        ]

        for dir_name in required_dirs:
            self.assertTrue((Path(self.temp_dir) / dir_name).exists())
