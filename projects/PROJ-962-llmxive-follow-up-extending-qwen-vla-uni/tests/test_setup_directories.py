import unittest
import os
import sys
import tempfile
import shutil

# Add the project root to the path so we can import code.setup_directories
# assuming this test runs from the repo root or tests/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.setup_directories import create_directories

class TestSetupDirectories(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to act as the project root for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the structure by creating a 'code' folder inside temp_dir to simulate root
        # Actually, the function calculates base_dir relative to itself.
        # We need to ensure the test environment mimics the expected layout or 
        # we test the logic differently.
        
        # Since create_directories() relies on os.path.dirname(os.path.dirname(...)),
        # it assumes it is run from within code/setup_directories.py.
        # In a real run, base_dir = project_root.
        # Here, we will patch os.path.abspath or simply verify the logic by 
        # running the function and checking if the dirs exist relative to the script.
        
        # To make this test robust without mocking paths deeply, we will just
        # run the function and verify the side effects in the actual project structure
        # if we were running integration tests. 
        # For unit testing logic:
        pass

    def tearDown(self):
        """Remove the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_directory_creation_logic(self):
        """
        Verify that create_directories returns a list of paths and that
        the paths contain the expected directory names.
        """
        # We call the function. In a real repo, this creates the dirs.
        # We verify the return value structure.
        result = create_directories()
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        expected_dirs = [
            "code", "code/utils", "code/tests", 
            "data/raw", "data/processed", "data/results", 
            "artifacts/models"
        ]
        
        for expected in expected_dirs:
            found = any(expected in path for path in result)
            self.assertTrue(found, f"Expected directory {expected} not found in results")

    def test_actual_directory_existence(self):
        """
        Verify that the directories actually exist on the filesystem after calling the function.
        This assumes the test is run from the project root or the script location is correct.
        """
        # Re-run to ensure they exist
        create_directories()
        
        # Determine the base directory based on the script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # The script is in tests/, so project root is parent of tests
        project_root = os.path.dirname(script_dir)
        
        expected_dirs = [
            "code", "code/utils", "code/tests", 
            "data/raw", "data/processed", "data/results", 
            "artifacts/models"
        ]
        
        for dir_name in expected_dirs:
            full_path = os.path.join(project_root, dir_name)
            self.assertTrue(os.path.isdir(full_path), 
                          f"Directory {full_path} does not exist after create_directories()")

if __name__ == "__main__":
    unittest.main()