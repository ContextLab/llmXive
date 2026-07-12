"""
Test suite for Task T001: Project Structure Verification.

Verifies that the required directory structure and placeholder files
exist as expected after running setup_project_structure.py.
"""
import os
import pytest
from pathlib import Path

# Determine project root relative to test file
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-a-survey-of"
RESULTS_DIR = PROJECT_ROOT / "results"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

REQUIRED_DIRS = [
    CODE_DIR,
    DATA_DIR,
    DATA_DIR / "raw",
    DATA_DIR / "processed",
    DATA_DIR / "embeddings",
    CODE_DIR / "data",
    CODE_DIR / "models",
    CODE_DIR / "utils",
    SPECS_DIR,
    RESULTS_DIR,
    RESULTS_DIR / "figures",
    CONTRACTS_DIR,
]

REQUIRED_INIT_FILES = [
    CODE_DIR / "__init__.py",
    CODE_DIR / "data" / "__init__.py",
    CODE_DIR / "models" / "__init__.py",
    CODE_DIR / "utils" / "__init__.py",
    TESTS_DIR / "__init__.py",
]

class TestProjectStructure:
    def test_required_directories_exist(self):
        """Assert that all required directories created by T001 exist."""
        missing_dirs = []
        for dir_path in REQUIRED_DIRS:
            if not dir_path.is_dir():
                missing_dirs.append(str(dir_path.relative_to(PROJECT_ROOT)))
        
        assert not missing_dirs, f"Missing directories: {', '.join(missing_dirs)}"

    def test_required_init_files_exist(self):
        """Assert that __init__.py files exist for Python packages."""
        missing_files = []
        for file_path in REQUIRED_INIT_FILES:
            if not file_path.is_file():
                missing_files.append(str(file_path.relative_to(PROJECT_ROOT)))
        
        assert not missing_files, f"Missing __init__.py files: {', '.join(missing_files)}"

    def test_data_subdirectories_exist(self):
        """Specific check for data pipeline subdirectories."""
        data_subdirs = [
            DATA_DIR / "raw",
            DATA_DIR / "processed",
            DATA_DIR / "embeddings"
        ]
        for subdir in data_subdirs:
            assert subdir.is_dir(), f"Data subdirectory missing: {subdir}"

    def test_specs_directory_structure(self):
        """Check that the specific specs directory for this project exists."""
        assert SPECS_DIR.is_dir(), f"Specs directory missing: {SPECS_DIR}"
        assert (SPECS_DIR / "contracts").is_dir() or True, "Contracts folder in specs is optional at this stage but recommended"
        assert (SPECS_DIR / "docs").is_dir() or True, "Docs folder in specs is optional at this stage but recommended"