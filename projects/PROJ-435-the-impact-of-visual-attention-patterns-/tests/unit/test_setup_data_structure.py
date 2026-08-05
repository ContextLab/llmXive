import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Add the parent directory to the path to import the module
sys_path_backup = list(__import__('sys').path)
try:
    # Assuming tests are in tests/unit and script is in code/
    # We need to add the project root to sys.path
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    __import__('sys').path.insert(0, str(project_root))
    
    from code.setup_data_structure import get_project_root, create_directories
finally:
    __import__('sys').path = sys_path_backup


class TestSetupDataStructure:
    """Tests for the data directory structure setup."""

    def test_get_project_root(self):
        """Test that get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_create_directories(self):
        """Test that create_directories creates the required folders."""
        # Create a temporary directory to simulate project root
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            
            # Define expected directories relative to temp_path
            expected_dirs = [
                "data/raw",
                "data/derived",
                "data/processed",
                "tests",
                "state",
                "output"
            ]
            
            # Verify they don't exist yet
            for d in expected_dirs:
                assert not (temp_path / d).exists()
            
            # Create them
            create_directories(temp_path, __import__('logging').getLogger("test"))
            
            # Verify they exist
            for d in expected_dirs:
                dir_path = temp_path / d
                assert dir_path.exists(), f"Directory {d} was not created."
                assert dir_path.is_dir(), f"{d} exists but is not a directory."

    def test_create_directories_idempotent(self):
        """Test that running create_directories twice does not error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            
            # Run once
            create_directories(temp_path, __import__('logging').getLogger("test"))
            
            # Run again - should not raise
            create_directories(temp_path, __import__('logging').getLogger("test"))
            
            # Verify still exists
            assert (temp_path / "data/raw").exists()