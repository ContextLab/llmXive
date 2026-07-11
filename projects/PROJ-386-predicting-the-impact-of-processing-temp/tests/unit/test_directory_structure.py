"""
Unit tests for project directory structure validation.
Specifically tests the existence of the data/raw directory created in T001b.
"""
import os
import unittest
from pathlib import Path

class TestDirectoryStructure(unittest.TestCase):
    """Tests to verify the project directory structure is correctly initialized."""

    def test_data_raw_directory_exists(self):
        """Verify that the data/raw directory exists."""
        # Determine the project root (assuming tests are in tests/unit/)
        # Project root is two levels up from tests/unit/
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        raw_data_dir = project_root / "data" / "raw"
        
        self.assertTrue(
            raw_data_dir.exists() and raw_data_dir.is_dir(),
            f"Directory {raw_data_dir} does not exist. Task T001b may not have been completed."
        )

    def test_data_raw_is_writeable(self):
        """Verify that the data/raw directory is writeable (optional check)."""
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        raw_data_dir = project_root / "data" / "raw"
        
        # Check if we can create a temporary file
        test_file = raw_data_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            self.assertTrue(True)
        except (OSError, IOError):
            self.fail(f"Directory {raw_data_dir} is not writeable.")

if __name__ == '__main__':
    unittest.main()