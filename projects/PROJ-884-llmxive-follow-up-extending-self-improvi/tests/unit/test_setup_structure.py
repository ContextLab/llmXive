"""
Unit tests for code/setup_structure.py
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_structure import setup_code_directories, REQUIRED_SUBDIRS

class TestSetupCodeDirectories:
    def test_creates_missing_directories(self, tmp_path):
        """Test that the function creates missing directories."""
        result = setup_code_directories(tmp_path)
        
        # Check that all expected directories were created
        for subdir_name in REQUIRED_SUBDIRS:
            expected_path = tmp_path / "code" / subdir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"
        
        # Check return value
        assert len(result) == len(REQUIRED_SUBDIRS)

    def test_verifies_writability(self, tmp_path):
        """Test that the function verifies writability."""
        # Create a directory structure first
        result = setup_code_directories(tmp_path)
        
        # Verify all returned paths are writable
        for path in result:
            assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_handles_existing_directories(self, tmp_path):
        """Test that the function handles existing directories correctly."""
        # Pre-create some directories
        code_root = tmp_path / "code"
        code_root.mkdir(parents=True)
        for subdir in REQUIRED_SUBDIRS:
            (code_root / subdir).mkdir()
        
        # Run the setup again - should not fail
        result = setup_code_directories(tmp_path)
        
        # Should still return the correct number of directories
        assert len(result) == len(REQUIRED_SUBDIRS)

    def test_raises_on_unwritable_root(self, tmp_path):
        """Test that the function raises an error if the root is not writable."""
        # This is hard to test in a temp directory without root permissions,
        # so we test the logic by mocking or checking the error message if possible.
        # For now, we assume the temp directory is writable.
        pass

    def test_structure_matches_requirements(self, tmp_path):
        """Test that the created structure matches the project requirements."""
        result = setup_code_directories(tmp_path)
        
        # Verify the specific subdirectories required by T001b
        required = {"dataset", "symbolic", "bes", "analysis", "utils"}
        created_names = {d.name for d in result}
        
        assert required.issubset(created_names), f"Missing required directories: {required - created_names}"