import unittest
import os
from pathlib import Path
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def test_directory_creation(self):
        """
        Verify that T001 creates the required directory structure.
        """
        # Run the creation logic
        base_path = Path(__file__).resolve().parent.parent
        create_directories()
        
        # Define expected directories relative to project root
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts",
        ]
        
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            self.assertTrue(
                dir_path.exists(), 
                f"Expected directory {dir_path} does not exist."
            )
            self.assertTrue(
                dir_path.is_dir(), 
                f"{dir_path} exists but is not a directory."
            )

if __name__ == "__main__":
    unittest.main()