import os
import pytest
import shutil
import tempfile
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_directories import create_directories

class TestDirectoryCreation:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Create a temporary directory to simulate the project root,
        run the creation logic, and then clean up.
        """
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            os.chdir(original_dir)
            # Clean up the temporary directory
            shutil.rmtree(self.temp_dir)

    def test_state_directory_exists(self):
        """
        Test that the 'state/' directory is created by the setup script.
        This directly validates T001c.
        """
        # Run the directory creation logic
        create_directories()
        
        # Assert that the state directory exists
        assert os.path.isdir("state"), "The 'state/' directory was not created."

    def test_all_required_directories_exist(self):
        """
        Test that all required project directories are created.
        """
        create_directories()
        
        required_dirs = [
            "code",
            "code/ingest",
            "code/features",
            "code/models",
            "code/viz",
            "code/utils",
            "tests",
            "data/raw",
            "data/processed",
            "data/artifacts",
            "state"
        ]
        
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"The directory '{dir_path}' was not created."