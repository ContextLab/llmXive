import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to simulate the environment where the script runs.
# Since we cannot import from 'code/setup_project_structure' directly in a test 
# without modifying sys.path, we will test the logic by importing the function 
# after adding the parent of 'code' to the path, or by copying the logic.
# However, the cleanest way for this specific task is to import the module 
# assuming the test runner is at the project root.

import sys
from pathlib import Path

# Add the project root to sys.path if not already there
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module to test
from code.setup_project_structure import create_directories, main

class TestSetupProjectStructure:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Setup a temporary directory structure that mimics the project root.
        'code' directory will be created under tmp_path.
        """
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # Create the 'code' directory to match expected structure
        (tmp_path / "code").mkdir()
        
        yield tmp_path
        
        os.chdir(self.original_cwd)

    def test_create_directories_success(self, tmp_path):
        """Test that all required subdirectories are created."""
        code_dir = tmp_path / "code"
        
        result = create_directories()
        
        assert result is True
        
        expected_dirs = [
            "data_download",
            "manipulation",
            "preprocess",
            "analysis",
            "visualization",
            "utils",
            "pipeline"
        ]
        
        for dir_name in expected_dirs:
            dir_path = code_dir / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_create_directories_idempotent(self, tmp_path):
        """Test that running the function twice does not cause errors."""
        result_first = create_directories()
        result_second = create_directories()
        
        assert result_first is True
        assert result_second is True

    def test_main_execution(self, tmp_path, capsys):
        """Test the main entry point."""
        # main() calls create_directories and prints success
        try:
            main()
            captured = capsys.readouterr()
            assert "completed successfully" in captured.out
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"main() exited with code {e.code}")

    def test_structure_exists(self, tmp_path):
        """Verify the exact paths match the task requirements."""
        create_directories()
        
        code_base = tmp_path / "code"
        
        # Check specific paths required by T001c
        required_paths = [
            code_base / "data_download",
            code_base / "manipulation",
            code_base / "preprocess",
            code_base / "analysis",
            code_base / "visualization",
            code_base / "utils",
            code_base / "pipeline"
        ]
        
        for p in required_paths:
            assert p.exists(), f"Missing required path: {p}"