"""
Test suite to verify project directory structure creation.

This test ensures that all required directories and __init__.py files
exist as specified in T001a, T001b, T001c, and T002a.
"""
import os
import pytest
from pathlib import Path

class TestProjectStructure:
    """Tests for project directory structure."""

    def test_code_directories_exist(self):
        """Verify code/ and its subdirectories exist."""
        required_dirs = [
            "code",
            "code/ingest",
            "code/features",
            "code/models",
            "code/viz",
            "code/utils",
        ]
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Directory missing: {dir_path}"

    def test_tests_directory_exists(self):
        """Verify tests/ directory exists."""
        assert os.path.isdir("tests"), "tests/ directory missing"

    def test_data_directories_exist(self):
        """Verify data/ and its subdirectories exist."""
        required_dirs = [
            "data",
            "data/raw",
            "data/processed",
            "data/artifacts",
        ]
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Directory missing: {dir_path}"

    def test_state_directory_exists(self):
        """Verify state/ directory exists."""
        assert os.path.isdir("state"), "state/ directory missing"

    def test_init_files_exist_in_code_subdirs(self):
        """Verify __init__.py files exist in all code/ subdirectories."""
        code_subdirs = ["ingest", "features", "models", "viz", "utils"]
        for subdir in code_subdirs:
            init_path = os.path.join("code", subdir, "__init__.py")
            assert os.path.isfile(init_path), f"Missing __init__.py: {init_path}"

    def test_init_files_exist_in_tests(self):
        """Verify __init__.py file exists in tests/."""
        init_path = os.path.join("tests", "__init__.py")
        assert os.path.isfile(init_path), f"Missing __init__.py: {init_path}"

    def test_init_file_exists_in_code_root(self):
        """Verify __init__.py file exists in code/ root."""
        init_path = os.path.join("code", "__init__.py")
        assert os.path.isfile(init_path), f"Missing __init__.py: {init_path}"

    def test_init_files_exist_in_data_subdirs(self):
        """Verify __init__.py files exist in data/ subdirectories."""
        data_subdirs = ["raw", "processed", "artifacts"]
        for subdir in data_subdirs:
            init_path = os.path.join("data", subdir, "__init__.py")
            assert os.path.isfile(init_path), f"Missing __init__.py: {init_path}"

    def test_directory_structure_is_complete(self):
        """Comprehensive test for complete directory structure."""
        all_required_dirs = [
            "code", "code/ingest", "code/features", "code/models", 
            "code/viz", "code/utils", "tests", "data", "data/raw", 
            "data/processed", "data/artifacts", "state"
        ]
        
        missing_dirs = []
        for dir_path in all_required_dirs:
            if not os.path.isdir(dir_path):
                missing_dirs.append(dir_path)
        
        assert not missing_dirs, f"Missing directories: {missing_dirs}"
