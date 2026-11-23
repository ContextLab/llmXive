"""
Integration test for the full project setup workflow.
Verifies that the directory structure is created and valid for subsequent tasks.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_project import create_directories, verify_directories
from utils import setup_logging

setup_logging(level="INFO")

class TestSetupIntegration:
    def test_full_setup_workflow(self, tmp_path):
        """
        Integration test: Run the full setup workflow and verify the structure.
        This simulates the actual execution of T001a.
        """
        # Act: Create directories
        created = create_directories(base_path=tmp_path)
        
        # Assert: Creation phase
        assert len(created) > 0, "Directories should have been created"
        
        # Assert: Verification phase
        is_valid = verify_directories(base_path=tmp_path)
        assert is_valid, "All directories should exist after creation"
        
        # Assert: Specific required paths exist
        required_paths = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "state"
        ]
        
        for path_str in required_paths:
            full_path = tmp_path / path_str
            assert full_path.exists(), f"Missing path: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"

    def test_setup_allows_subsequent_file_writing(self, tmp_path):
        """
        Integration test: Ensure the created structure allows writing files.
        This validates that the directories are writable and correctly configured.
        """
        # Setup
        create_directories(base_path=tmp_path)
        
        # Act: Try to write a test file into data/processed
        test_file = tmp_path / "data" / "processed" / "test_write.txt"
        try:
            with open(test_file, 'w') as f:
                f.write("Test content")
            # Assert
            assert test_file.exists(), "Test file should be writable"
            assert test_file.read_text() == "Test content"
        except Exception as e:
            pytest.fail(f"Failed to write to created directory structure: {e}")