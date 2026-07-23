import os
import shutil
import tempfile
import pytest
from pathlib import Path

# Import the function to test
# We assume the test runner adds 'code' to sys.path or we import relatively if structure allows
# Given the task context, we import from the module file directly
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import create_directories


class TestCreateDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for testing and clean up after."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_creates_all_required_directories(self):
        """Test that all required directories are created."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "state"
        ]
        
        result = create_directories()
        
        for dir_name in required_dirs:
            assert dir_name in result, f"Directory {dir_name} not in result keys"
            full_path = Path(self.temp_dir) / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_nested_directories_created(self):
        """Test that nested directories like data/raw are created correctly."""
        result = create_directories()
        
        # Check nested paths
        nested_paths = ["data/raw", "data/processed", "data/reports"]
        for path_str in nested_paths:
            full_path = Path(self.temp_dir) / path_str
            assert full_path.exists(), f"Nested directory {full_path} was not created"

    def test_idempotent(self):
        """Test that running the function twice does not raise errors."""
        # First run
        create_directories()
        
        # Second run
        try:
            result = create_directories()
            assert True  # If no exception, it's idempotent
        except Exception as e:
            pytest.fail(f"Function raised exception on second run: {e}")

    def test_returns_absolute_paths(self):
        """Test that the returned dictionary contains absolute paths."""
        result = create_directories()
        
        for path_str in result.values():
            assert os.path.isabs(path_str), f"Path {path_str} is not absolute"
