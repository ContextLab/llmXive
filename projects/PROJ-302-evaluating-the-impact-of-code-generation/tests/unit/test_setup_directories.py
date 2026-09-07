import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import create_directories

class TestSetupDirectories:
    """
    Unit tests for the setup_directories module.
    Verifies that the required directory structure is created correctly.
    """

    def test_create_directories_in_temp_dir(self):
        """Test that create_directories creates all required directories in a temp location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Call the function
            result = create_directories(base_path)
            
            # Assert success
            assert result is True, "create_directories should return True on success"
            
            # Verify each required directory exists
            required_dirs = [
                "code",
                "data/tests",
                "docs",
                "data/raw",
                "data/processed"
            ]
            
            for dir_name in required_dirs:
                full_path = base_path / dir_name
                assert full_path.exists(), f"Directory {full_path} should exist"
                assert full_path.is_dir(), f"{full_path} should be a directory"

    def test_create_directories_idempotent(self):
        """Test that running create_directories twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Run twice
            result1 = create_directories(base_path)
            result2 = create_directories(base_path)
            
            # Both should succeed
            assert result1 is True
            assert result2 is True

    def test_create_directories_creates_parent_dirs(self):
        """Test that nested directories are created with parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            result = create_directories(base_path)
            assert result is True
            
            # Check nested structure
            data_tests = base_path / "data" / "tests"
            assert data_tests.exists()
            assert data_tests.is_dir()
            
            # Check that 'data' itself exists
            data_dir = base_path / "data"
            assert data_dir.exists()
            assert data_dir.is_dir()

    def test_create_directories_with_existing_dirs(self):
        """Test that existing directories don't cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Pre-create one of the directories
            (base_path / "code").mkdir()
            
            # Should still succeed
            result = create_directories(base_path)
            assert result is True

    def test_create_directories_structure(self):
        """Test the exact structure of created directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            create_directories(base_path)
            
            # Verify the exact tree structure
            expected_structure = {
                "code": [],
                "data": {
                    "tests": [],
                    "raw": [],
                    "processed": []
                },
                "docs": []
            }
            
            def verify_structure(current_path, structure):
                for key, value in structure.items():
                    path = current_path / key
                    assert path.exists(), f"Missing: {path}"
                    assert path.is_dir(), f"Not a directory: {path}"
                    if isinstance(value, dict):
                        verify_structure(path, value)
            
            verify_structure(base_path, expected_structure)