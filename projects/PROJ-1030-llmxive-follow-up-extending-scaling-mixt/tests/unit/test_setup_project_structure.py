import os
import sys
import pytest
from pathlib import Path
import shutil

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_directories

class TestProjectStructure:
    """
    Tests for the project structure creation task (T001).
    Verifies that all required directories are created.
    """
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Set up a temporary directory to run tests in isolation.
        """
        self.original_cwd = Path.cwd()
        os.chdir(tmp_path)
        yield
        os.chdir(self.original_cwd)
    
    def test_required_directories_created(self):
        """
        Verify that all directories specified in T001 are created.
        Required: code, code/utils, data/raw, data/processed, 
                tests/unit, tests/integration, docs/figures, state
        """
        required_dirs = [
            "code",
            "code/utils",
            "data/raw",
            "data/processed",
            "tests/unit",
            "tests/integration",
            "docs/figures",
            "state"
        ]
        
        # Run the creation function
        result = create_directories()
        
        assert result is True, "create_directories should return True on success"
        
        base_dir = Path.cwd()
        
        for dir_name in required_dirs:
            dir_path = base_dir / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"
    
    def test_nested_directory_structure(self):
        """
        Verify that nested directories (e.g., code/utils) are created correctly.
        """
        create_directories()
        
        base_dir = Path.cwd()
        
        # Check nested paths
        nested_paths = [
            "code/utils",
            "data/raw",
            "data/processed",
            "tests/unit",
            "tests/integration",
            "docs/figures"
        ]
        
        for path_str in nested_paths:
            dir_path = base_dir / path_str
            assert dir_path.exists(), f"Nested directory {dir_path} was not created"
    
    def test_idempotency(self):
        """
        Verify that running the script multiple times does not cause errors.
        """
        # First run
        result1 = create_directories()
        assert result1 is True
        
        # Second run (should handle existing directories gracefully)
        result2 = create_directories()
        assert result2 is True
        
        # Verify directories still exist
        base_dir = Path.cwd()
        assert (base_dir / "code").exists()
        assert (base_dir / "data/processed").exists()
        assert (base_dir / "state").exists()