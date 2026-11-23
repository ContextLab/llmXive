import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add code directory to path for imports
current_dir = Path(__file__).resolve().parent
code_dir = current_dir.parent
sys.path.insert(0, str(code_dir))

from setup_directories import create_data_directories


class TestSetupDirectories(unittest.TestCase):
    """Test cases for T002: Data directory creation."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_data_directories_created(self):
        """Verify that all required data directories are created."""
        create_data_directories(self.project_root)
        
        # Check that data/raw exists
        raw_dir = self.project_root / "data" / "raw"
        self.assertTrue(raw_dir.exists(), "data/raw directory was not created")
        self.assertTrue(raw_dir.is_dir(), "data/raw is not a directory")

        # Check that data/processed exists
        processed_dir = self.project_root / "data" / "processed"
        self.assertTrue(processed_dir.exists(), "data/processed directory was not created")
        self.assertTrue(processed_dir.is_dir(), "data/processed is not a directory")

        # Check that data/reports exists
        reports_dir = self.project_root / "data" / "reports"
        self.assertTrue(reports_dir.exists(), "data/reports directory was not created")
        self.assertTrue(reports_dir.is_dir(), "data/reports is not a directory")

    def test_existing_directories_not_recreated(self):
        """Verify that existing directories are handled gracefully."""
        # Create one directory beforehand
        existing_dir = self.project_root / "data" / "raw"
        existing_dir.mkdir(parents=True)
        
        # Should not raise an error
        create_data_directories(self.project_root)
        
        # Verify the directory still exists and is a directory
        self.assertTrue(existing_dir.exists())
        self.assertTrue(existing_dir.is_dir())

    def test_nested_directory_creation(self):
        """Verify that nested directories are created with parents=True."""
        # Don't create parent 'data' directory beforehand
        create_data_directories(self.project_root)
        
        # All three should exist
        self.assertTrue((self.project_root / "data").exists())
        self.assertTrue((self.project_root / "data" / "raw").exists())
        self.assertTrue((self.project_root / "data" / "processed").exists())
        self.assertTrue((self.project_root / "data" / "reports").exists())


if __name__ == "__main__":
    unittest.main()