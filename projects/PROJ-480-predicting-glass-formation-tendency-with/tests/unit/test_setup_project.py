"""
Unit tests for the project setup script (T001).

These tests verify that the directory structure is created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the main function from the setup script
# We need to adjust the path to import code/setup_project
import sys
import importlib.util

# Load setup_project module dynamically
spec = importlib.util.spec_from_file_location("setup_project", "code/setup_project.py")
setup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_module)


class TestProjectStructure:
    """Test cases for verifying project directory creation."""

    def test_directories_exist_after_setup(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup logic
            setup_module.main()
            
            # Define expected directories relative to tmp_path
            expected_dirs = [
                "src/data",
                "src/models",
                "src/reports",
                "src/cli",
                "src/lib",
                "tests/contract",
                "tests/unit",
                "tests/integration",
                "data/raw",
                "data/processed",
                "state",
                "reports",
            ]
            
            # Verify each directory exists
            for dir_path in expected_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_nested_directories_created(self, tmp_path):
        """Verify that nested directory structures are created correctly."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            setup_module.main()
            
            # Check specific nested paths
            src_lib = tmp_path / "src" / "lib"
            assert src_lib.exists()
            
            tests_contract = tmp_path / "tests" / "contract"
            assert tests_contract.exists()
            
            data_processed = tmp_path / "data" / "processed"
            assert data_processed.exists()
        finally:
            os.chdir(original_cwd)

    def test_idempotent_creation(self, tmp_path):
        """Verify that running setup twice doesn't cause errors."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            setup_module.main()
            setup_module.main()
            
            # Verify directories still exist
            expected_dirs = ["src", "data", "tests", "state", "reports"]
            for dir_name in expected_dirs:
                assert (tmp_path / dir_name).exists()
        finally:
            os.chdir(original_cwd)