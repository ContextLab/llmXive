"""
Unit tests for project structure initialization.

These tests verify that the required directory structure exists
and is correctly formatted as per the project specification.
"""
import os
import pytest
from pathlib import Path

# Helper to get the project root (assumes tests/ is at root or code/tests is inside)
# We assume this file is run from the project root or one level up.
# Adjust based on actual execution context.
ROOT = Path(__file__).resolve().parent.parent

def get_path(rel_path):
    return ROOT / rel_path

class TestProjectStructure:
    """Tests for the existence of required project directories."""

    def test_code_directory_exists(self):
        """Verify that the 'code' directory exists."""
        assert get_path("code").exists(), "Directory 'code' does not exist."
        assert get_path("code").is_dir(), "'code' is not a directory."

    def test_data_directory_exists(self):
        """Verify that the 'data' directory exists."""
        assert get_path("data").exists(), "Directory 'data' does not exist."
        assert get_path("data").is_dir(), "'data' is not a directory."

    def test_results_directory_exists(self):
        """Verify that the 'results' directory exists."""
        assert get_path("results").exists(), "Directory 'results' does not exist."
        assert get_path("results").is_dir(), "'results' is not a directory."

    def test_tests_directory_exists(self):
        """Verify that the 'tests' directory exists."""
        assert get_path("tests").exists(), "Directory 'tests' does not exist."
        assert get_path("tests").is_dir(), "'tests' is not a directory."

    def test_data_subdirectories_exist(self):
        """Verify that required data subdirectories exist."""
        required_subdirs = [
            "data/raw",
            "data/processed",
            "data/external"
        ]
        for subdir in required_subdirs:
            path = get_path(subdir)
            assert path.exists(), f"Required subdirectory '{subdir}' does not exist."
            assert path.is_dir(), f"'{subdir}' is not a directory."

    def test_results_subdirectories_exist(self):
        """Verify that required results subdirectories exist."""
        required_subdirs = [
            "results/associations",
            "results/sensitivity",
            "results/validation",
            "results/plots"
        ]
        for subdir in required_subdirs:
            path = get_path(subdir)
            assert path.exists(), f"Required subdirectory '{subdir}' does not exist."
            assert path.is_dir(), f"'{subdir}' is not a directory."

    def test_code_subdirectories_exist(self):
        """Verify that required code subdirectories exist."""
        required_subdirs = [
            "code/models",
            "code/utils",
            "code/validation"
        ]
        for subdir in required_subdirs:
            path = get_path(subdir)
            assert path.exists(), f"Required subdirectory '{subdir}' does not exist."
            assert path.is_dir(), f"'{subdir}' is not a directory."

    def test_structure_is_callable(self):
        """Verify that the create_structure module can be imported and run."""
        try:
            # Import the module to ensure it's syntactically correct
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "create_structure", get_path("code/create_structure.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Verify main function exists
            assert hasattr(module, "main"), "create_structure.py must have a 'main' function."
        except ImportError as e:
            pytest.fail(f"Failed to import create_structure.py: {e}")