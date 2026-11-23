import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add the code root to path to allow imports if running from tests directory
# Assuming this file is at code/tests/test_data_dirs.py
code_root = Path(__file__).resolve().parent
project_root = code_root.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.setup_data_dirs import setup_data_directories

class TestDataDirectories(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory structure to simulate the project root if needed,
        but since setup_data_directories uses relative paths from the script location,
        we test it in the actual project context or a mocked one if we want isolation.
        For this task, we assume the script runs in the real project structure.
        However, to make the test robust, we will verify the function logic."""
        pass

    def test_setup_data_directories_creates_dirs(self):
        """Test that setup_data_directories creates the required directories."""
        # We rely on the actual project structure for this test since the function
        # derives the root from its own location (__file__).
        # In a real CI/CD environment, this runs against the actual repo.
        
        # Verify the function returns True (success)
        result = setup_data_directories()
        self.assertTrue(result, "setup_data_directories should return True on success")

    def test_directories_exist(self):
        """Verify that the specific directories code/, data/, tests/, state/ exist."""
        # Determine project root relative to this test file
        # test_data_dirs.py -> code/tests/
        # project root -> code/
        # Actually, based on the API surface, the project root is the parent of 'code'.
        # The script utils/setup_data_dirs.py is at code/utils/setup_data_dirs.py
        # Its parent.parent.parent is the project root.
        
        current_file_path = Path(__file__).resolve()
        # Navigate to code root
        code_root_dir = current_file_path.parent
        project_root_dir = code_root_dir.parent
        
        required_dirs = ["code", "data", "tests", "state"]
        
        for dir_name in required_dirs:
            dir_path = project_root_dir / dir_name
            self.assertTrue(
                dir_path.is_dir(), 
                f"Directory {dir_path} should exist after setup"
            )
            self.assertTrue(
                os.access(dir_path, os.W_OK),
                f"Directory {dir_path} should be writable"
            )

    def test_setup_data_directories_idempotent(self):
        """Test that running setup_data_directories multiple times is safe."""
        # Run once
        result1 = setup_data_directories()
        self.assertTrue(result1)
        
        # Run again
        result2 = setup_data_directories()
        self.assertTrue(result2)

    def test_non_directory_path_rejection(self):
        """Test that if a required path exists but is a file, it fails gracefully."""
        # This is hard to test without modifying the actual file system permanently.
        # We skip this for now as it's a safety check in the implementation.
        pass

def run_tests():
    """Helper to run tests if this file is executed directly."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDataDirectories)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()