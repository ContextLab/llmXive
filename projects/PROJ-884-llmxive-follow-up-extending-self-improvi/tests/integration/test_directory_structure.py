"""
Integration test to verify the complete directory structure setup.

This test ensures that the entire project directory hierarchy
(code/, data/, tests/) is correctly established and writable.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

from code.setup_tests import setup_tests_directories
from code.setup_data_dirs import setup_data_directories
from code.setup_structure import setup_code_directories


class TestCompleteDirectoryStructure:
    """Integration tests for the full project directory structure."""

    def test_full_structure_creation(self, tmp_path):
        """Verify that all major directory trees can be created."""
        # Setup data directories
        data_dirs = setup_data_directories(tmp_path)
        
        # Setup code directories
        code_dirs = setup_code_directories(tmp_path)
        
        # Setup tests directories
        tests_dirs = setup_tests_directories(tmp_path)
        
        # Verify all expected top-level directories exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "code").exists()
        assert (tmp_path / "tests").exists()
        
        # Verify tests subdirectories
        assert (tmp_path / "tests" / "unit").exists()
        assert (tmp_path / "tests" / "integration").exists()

    def test_all_directories_writable(self, tmp_path):
        """Verify that all created directories are writable."""
        # Create all structures
        setup_data_directories(tmp_path)
        setup_code_directories(tmp_path)
        setup_tests_directories(tmp_path)
        
        # Test write capability in tests directories
        for subdir in ["unit", "integration"]:
            test_file = tmp_path / "tests" / subdir / "integration_test.txt"
            try:
                test_file.write_text("Integration test content")
                assert test_file.read_text() == "Integration test content"
            finally:
                if test_file.exists():
                    test_file.unlink()

    def test_no_collision_with_existing_files(self, tmp_path):
        """Verify setup handles existing files gracefully where possible."""
        # Create a dummy file in the root
        dummy_file = tmp_path / "tests.txt"
        dummy_file.write_text("dummy")
        
        # Setup should still succeed for directories
        result = setup_tests_directories(tmp_path)
        assert len(result) == 3
        assert dummy_file.exists()  # Original file untouched
        assert (tmp_path / "tests").exists()