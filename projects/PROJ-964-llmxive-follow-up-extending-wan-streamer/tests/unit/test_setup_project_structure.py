import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import the module
# Assuming this test runs from the project root
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from tasks.setup_project_structure import create_directory_structure, verify_directories, PROJECT_PATH

class TestSetupProjectStructure:
    """
    Unit tests for the project structure setup task (T005).
    Verifies that the directory structure is created correctly.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Ensure we are testing in a clean environment if needed,
        though we rely on the actual PROJECT_PATH for the real test.
        Teardown: No teardown needed as we are creating directories.
        """
        # We are testing the actual project path, so we just run the logic
        yield

    def test_create_structure_success(self):
        """
        Test that create_directory_structure successfully creates the required folders.
        """
        success, created_paths = create_directory_structure()
        
        assert success is True, "Directory creation should return success=True"
        assert len(created_paths) > 0, "At least one directory should be created"
        
        # Verify specific critical paths exist
        required_subdirs = [
            "code", "data", "state", "docs", "specs", "contracts", "figures"
        ]
        
        for subdir in required_subdirs:
            full_path = PROJECT_PATH / subdir
            assert os.path.isdir(full_path), f"Directory {full_path} should exist after creation"

    def test_verify_directories_all_exist(self):
        """
        Test that verify_directories returns True after creation.
        """
        # First ensure creation has happened
        create_directory_structure()
        
        all_exist, missing = verify_directories()
        
        assert all_exist is True, "All directories should exist after creation"
        assert len(missing) == 0, f"No directories should be missing, but found: {missing}"

    def test_specific_project_path_exists(self):
        """
        Specific test for T005 verification requirement:
        Run os.path.exists and assert True on the project root.
        """
        assert os.path.exists(PROJECT_PATH), f"The project root {PROJECT_PATH} must exist"
        assert os.path.isdir(PROJECT_PATH), f"The project root {PROJECT_PATH} must be a directory"

    def test_nested_directories_exist(self):
        """
        Verify that nested directories like code/data and data/processed exist.
        """
        create_directory_structure()
        
        nested_paths = [
            "code/data",
            "code/models",
            "data/raw",
            "data/processed",
            "data/models"
        ]
        
        for subdir in nested_paths:
            full_path = PROJECT_PATH / subdir
            assert os.path.isdir(full_path), f"Nested directory {full_path} should exist"