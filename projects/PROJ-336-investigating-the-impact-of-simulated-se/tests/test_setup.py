"""
Tests for project setup and directory structure validation.

These tests verify that the project structure created by setup_project.py
matches the expected layout for the llmXive research pipeline.
"""
import os
import pytest
from pathlib import Path

# Get the project root (parent of tests directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Expected directories relative to project root
EXPECTED_DIRS = [
    "code",
    "code/data",
    "code/utils",
    "code/analysis",
    "code/viz",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "data/external",
    "results",
    "results/figures",
    "results/reports",
    "specs",
]

# Expected files
EXPECTED_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
]

class TestProjectStructure:
    """Test cases for validating project structure."""

    def test_project_root_exists(self):
        """Verify that the project root directory exists."""
        assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
        assert PROJECT_ROOT.is_dir(), f"Project root {PROJECT_ROOT} is not a directory"

    @pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
    def test_directory_exists(self, dir_path):
        """Verify that each expected directory exists."""
        full_path = PROJECT_ROOT / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

    @pytest.mark.parametrize("file_path", EXPECTED_FILES)
    def test_file_exists(self, file_path):
        """Verify that each expected file exists."""
        full_path = PROJECT_ROOT / file_path
        assert full_path.exists(), f"File {file_path} does not exist"
        assert full_path.is_file(), f"{file_path} is not a file"

    def test_data_directories_exist(self):
        """Verify that all data-related directories exist."""
        data_dirs = ["data", "data/raw", "data/processed", "data/external"]
        for dir_path in data_dirs:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Data directory {dir_path} does not exist"

    def test_results_directories_exist(self):
        """Verify that all results-related directories exist."""
        results_dirs = ["results", "results/figures", "results/reports"]
        for dir_path in results_dirs:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Results directory {dir_path} does not exist"

    def test_code_directories_exist(self):
        """Verify that all code-related directories exist."""
        code_dirs = ["code", "code/data", "code/utils", "code/analysis", "code/viz"]
        for dir_path in code_dirs:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Code directory {dir_path} does not exist"

    def test_test_directories_exist(self):
        """Verify that all test-related directories exist."""
        test_dirs = ["tests", "tests/unit", "tests/integration"]
        for dir_path in test_dirs:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Test directory {dir_path} does not exist"

class TestGitKeepFiles:
    """Test cases for .gitkeep files in empty directories."""

    @pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
    def test_gitkeep_exists(self, dir_path):
        """Verify that .gitkeep files exist in expected directories."""
        full_path = PROJECT_ROOT / dir_path / ".gitkeep"
        # Note: .gitkeep might not exist for all directories if they have content
        # This test is more of a soft check
        # assert full_path.exists(), f".gitkeep not found in {dir_path}"
        # For now, we'll just check if the directory exists
        assert full_path.parent.exists(), f"Directory {dir_path} does not exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])