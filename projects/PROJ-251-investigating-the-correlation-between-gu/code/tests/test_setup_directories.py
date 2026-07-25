import unittest
import os
from pathlib import Path
from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def test_directory_creation(self):
        """
        Verifies that the required directory structure is created by the setup script.
        """
        # Run the creation logic
        create_directories()
        
        # Define the expected paths relative to the project root
        # We assume the test is run from the project root or code/tests
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "specs/001-investigating-the-correlation-between-gu/contracts"
        ]
        
        for dir_name in required_dirs:
            full_path = project_root / dir_name
            self.assertTrue(
                full_path.exists(),
                f"Directory {full_path} was not created."
            )
            self.assertTrue(
                full_path.is_dir(),
                f"Path {full_path} exists but is not a directory."
            )

if __name__ == "__main__":
    unittest.main()