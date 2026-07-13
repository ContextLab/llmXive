import os
import pytest
import tempfile
import shutil
import sys

# Add the code directory to the path for imports
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "code")
sys.path.insert(0, code_dir)

from setup_project_structure import create_directory, DIRECTORIES

class TestProjectStructure:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory to test in, then clean up."""
        self.temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        yield
        os.chdir(original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_directory_exists(self):
        """Test that creating an existing directory returns True and doesn't error."""
        assert create_directory("test_dir")
        assert create_directory("test_dir")  # Should be idempotent

    def test_create_nested_directory(self):
        """Test creating a nested directory structure."""
        assert create_directory("parent/child/grandchild")
        assert os.path.isdir("parent/child/grandchild")

    def test_all_directories_created(self):
        """Test that all required directories can be created."""
        for dir_path in DIRECTORIES:
            # Change to a temp root for each test to simulate fresh start if needed,
            # but since we are in a temp dir, just ensure they are created relative to it.
            # Note: The actual script runs from root, so we simulate that here.
            # We adjust the path to be relative to the temp dir for this test.
            # The script logic is simple makedirs, so we test the function directly.
            assert create_directory(dir_path), f"Failed to create {dir_path}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    def test_directory_list_completeness(self):
        """Verify the DIRECTORIES list contains the required paths from T001."""
        required = {
            "code", "code/scheduler", "code/training", "code/analysis", "code/utils",
            "data/raw", "data/processed", "data/validation",
            "tests/unit", "tests/integration", "contracts"
        }
        actual = set(DIRECTORIES)
        assert required.issubset(actual), f"Missing directories: {required - actual}"