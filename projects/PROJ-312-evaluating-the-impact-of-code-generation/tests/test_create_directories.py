"""
Unit tests for the create_directories script (Task T001a).
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys
import unittest

# Add the code directory to the path to import the script
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_directories import main


class TestCreateDirectories(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the workspace root
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        # Restore original working directory and remove temp dir
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_directories_created(self):
        """Test that the required directories are created."""
        project_name = "PROJ-312-evaluating-the-impact-of-code-generation"
        expected_dirs = ["code", "data", "tests", "contracts", "artifacts", "state"]
        
        # Run the main function
        result = main()
        
        # Verify the project directory exists
        project_path = Path(self.temp_dir) / "projects" / project_name
        self.assertTrue(project_path.exists(), f"Project directory {project_path} was not created.")
        
        # Verify each subdirectory exists
        for subdir in expected_dirs:
            dir_path = project_path / subdir
            self.assertTrue(dir_path.exists(), f"Subdirectory {dir_path} was not created.")
            self.assertTrue(dir_path.is_dir(), f"{dir_path} is not a directory.")

    def test_directories_created_idempotent(self):
        """Test that running the script again doesn't fail."""
        # Run twice
        main()
        try:
            main()
        except Exception as e:
            self.fail(f"Running the script twice raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()