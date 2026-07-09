import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path to allow imports
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))

from setup_project_structure import create_directories

class TestSetupProjectStructure(unittest.TestCase):
    
    def setUp(self):
        """
        Create a temporary directory to simulate the project root.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a dummy code directory structure to mimic the project layout
        # so that the script can find its parent correctly
        os.makedirs("code", exist_ok=True)
        
    def tearDown(self):
        """
        Clean up the temporary directory.
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_directories(self):
        """
        Test that all required directories are created.
        """
        # Run the function
        result = create_directories()
        
        self.assertTrue(result, "create_directories should return True")
        
        # Define expected directories relative to the temp root
        expected_dirs = [
            "code/data_prep",
            "code/analysis",
            "code/utils",
            "code/tests",
            "data/defects4j",
            "data/summaries",
            "data/interaction_logs",
            "data/analysis_results",
            "data/consent",
            "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz"
        ]
        
        for dir_path in expected_dirs:
            full_path = Path(self.temp_dir) / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} should exist")
            self.assertTrue(full_path.is_dir(), f"{dir_path} should be a directory")

    def test_idempotency(self):
        """
        Test that running the function twice does not cause errors.
        """
        # Run twice
        result1 = create_directories()
        result2 = create_directories()
        
        self.assertTrue(result1)
        self.assertTrue(result2)

if __name__ == "__main__":
    unittest.main()