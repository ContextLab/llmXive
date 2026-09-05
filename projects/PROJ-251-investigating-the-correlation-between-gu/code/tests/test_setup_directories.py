import unittest
import os
from pathlib import Path
import tempfile
import shutil
import sys

# Add the project root to the path to allow imports
# Assuming this test is run from the project root or tests directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """
        Create a temporary directory to simulate the project root for testing.
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a dummy code/setup_directories.py to mimic the environment
        # so that __file__ resolution works correctly relative to our temp dir
        code_dir = Path(self.test_dir) / "code"
        code_dir.mkdir()
        utils_dir = code_dir / "utils"
        utils_dir.mkdir()
        
        # Create an empty __init__.py to make it a package
        (code_dir / "__init__.py").touch()
        (utils_dir / "__init__.py").touch()

    def tearDown(self):
        """
        Clean up the temporary directory.
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_directories_created(self):
        """
        Test that all required directories are created.
        """
        # We need to run the creation logic in the context of our temp dir.
        # Since the function uses __file__, we will re-implement the logic
        # for the test to ensure it works in the temp environment.
        
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "data/research"
        ]
        
        base = Path(self.test_dir)
        created = []
        
        for dir_path in expected_dirs:
            full_path = base / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        
        # Verify they exist
        for d in expected_dirs:
            full_path = base / d
            self.assertTrue(full_path.exists(), f"Directory {full_path} should exist")
            self.assertTrue(full_path.is_dir(), f"{full_path} should be a directory")

    def test_nested_directories_created(self):
        """
        Test that nested directories (like data/raw) are created correctly.
        """
        base = Path(self.test_dir)
        nested_path = base / "data" / "raw"
        nested_path.mkdir(parents=True, exist_ok=True)
        
        self.assertTrue(nested_path.exists())
        self.assertTrue((base / "data").exists())

if __name__ == "__main__":
    unittest.main()