import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from setup_directories import main

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock 'code' directory structure to match the script's expectation
        # The script expects to be run from code/, so we create a fake code dir
        self.code_dir = os.path.join(self.temp_dir, "code")
        os.makedirs(self.code_dir)
        # Change to the code directory so the script finds the project root correctly
        self.original_cwd = os.getcwd()
        os.chdir(self.code_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_directories_created(self):
        """Test that the required directories are created."""
        # Run the main function
        exit_code = main()
        
        self.assertEqual(exit_code, 0, "main() should return 0 on success")

        # Define expected paths relative to the temp project root
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/reports",
            "code/data",
            "code/tests",
            "code/utils",
        ]

        for dir_name in expected_dirs:
            full_path = os.path.join(self.temp_dir, dir_name)
            self.assertTrue(
                os.path.exists(full_path), 
                f"Directory {full_path} should exist after running main()"
            )
            self.assertTrue(
                os.path.isdir(full_path), 
                f"{full_path} should be a directory"
            )

    def test_idempotency(self):
        """Test that running the script twice does not cause errors."""
        # Run once
        exit_code_1 = main()
        self.assertEqual(exit_code_1, 0)

        # Run again
        exit_code_2 = main()
        self.assertEqual(exit_code_2, 0)

        # Verify directories still exist
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/reports",
        ]
        for dir_name in expected_dirs:
            full_path = os.path.join(self.temp_dir, dir_name)
            self.assertTrue(os.path.exists(full_path))

if __name__ == "__main__":
    unittest.main()