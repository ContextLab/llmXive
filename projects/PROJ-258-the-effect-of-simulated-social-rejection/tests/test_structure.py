"""
Test suite for verifying the project structure created by T001.
"""
import os
import pytest
from pathlib import Path

# Define expected directories and files
EXPECTED_DIRS = [
    "code",
    "data/raw",
    "data/interim",
    "data/processed",
    "figures",
    "reports",
    "tests",
    "docs",
    "specs",
    ".github/workflows"
]

EXPECTED_FILES = [
    "code/__init__.py",
    "code/config.py",
    "code/data_model.py",
    "code/ingest.py",
    "code/preprocess.py",
    "code/analysis.py",
    "code/report.py",
    "code/main.py",
    "tests/__init__.py",
    "tests/test_ingest.py",
    "tests/test_preprocess.py",
    "tests/test_analysis.py",
    "data/.gitkeep",
    "data/raw/.gitkeep",
    "data/interim/.gitkeep",
    "data/processed/.gitkeep",
    "figures/.gitkeep",
    "reports/.gitkeep",
    "docs/.gitkeep",
    "specs/.gitkeep",
    ".github/workflows/.gitkeep"
]

class TestProjectStructure:
    """Tests to verify the project structure exists as expected."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(".")

    def test_directories_exist(self, project_root):
        """Assert that all required directories exist."""
        for dir_name in EXPECTED_DIRS:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_files_exist(self, project_root):
        """Assert that all required placeholder files exist."""
        for file_name in EXPECTED_FILES:
            file_path = project_root / file_name
            assert file_path.exists(), f"File {file_path} does not exist"
            assert file_path.is_file(), f"{file_path} is not a file"

    def test_code_directory_structure(self, project_root):
        """Assert that the code directory contains expected Python modules."""
        code_dir = project_root / "code"
        required_modules = [
            "__init__.py", "config.py", "data_model.py", "ingest.py",
            "preprocess.py", "analysis.py", "report.py", "main.py"
        ]
        for module in required_modules:
            module_path = code_dir / module
            assert module_path.exists(), f"Module {module_path} is missing"

    def test_data_directory_hierarchy(self, project_root):
        """Assert that the data directory has the correct subdirectory hierarchy."""
        data_dir = project_root / "data"
        subdirs = ["raw", "interim", "processed"]
        for subdir in subdirs:
            subdir_path = data_dir / subdir
            assert subdir_path.exists(), f"Subdirectory {subdir_path} is missing"
            assert subdir_path.is_dir(), f"{subdir_path} is not a directory"

    def test_tests_directory_has_test_files(self, project_root):
        """Assert that the tests directory contains the required test files."""
        tests_dir = project_root / "tests"
        required_tests = [
            "test_ingest.py", "test_preprocess.py", "test_analysis.py"
        ]
        for test_file in required_tests:
            test_path = tests_dir / test_file
            assert test_path.exists(), f"Test file {test_path} is missing"
            assert test_path.is_file(), f"{test_path} is not a file"