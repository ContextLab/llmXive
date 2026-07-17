import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import main

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to simulate the project root
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Ensure no directories exist before the test
        dirs_to_check = [
            "data/raw", "data/processed", "output/plots",
            "code", "code/utils", "tests/unit", "tests/integration", "tests/contract"
        ]
        for d in dirs_to_check:
            path = Path(d)
            if path.exists():
                shutil.rmtree(path)

    def tearDown(self):
        # Restore original directory and clean up temp
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_main_creates_directories(self):
        """Verify that main() creates all required directories."""
        # Run the main function
        main()
        
        # Verify existence of all required directories
        required_dirs = [
            "data/raw", "data/processed", "output/plots",
            "code", "code/utils", "tests/unit", "tests/integration", "tests/contract"
        ]
        
        for dir_name in required_dirs:
            full_path = Path(dir_name)
            self.assertTrue(full_path.exists(), f"Directory {full_path} was not created.")
            self.assertTrue(full_path.is_dir(), f"{full_path} exists but is not a directory.")

    def test_code_utils_structure(self):
        """Specifically verify the code/utils hierarchy."""
        main()
        code_utils = Path("code/utils")
        self.assertTrue(code_utils.exists())
        self.assertTrue(code_utils.is_dir())

    def test_tests_structure(self):
        """Verify the test directory hierarchy."""
        main()
        self.assertTrue(Path("tests/unit").exists())
        self.assertTrue(Path("tests/integration").exists())
        self.assertTrue(Path("tests/contract").exists())

if __name__ == "__main__":
    unittest.main()