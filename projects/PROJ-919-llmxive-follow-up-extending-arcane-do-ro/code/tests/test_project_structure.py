"""
Test to verify the project structure is correctly set up.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the setup script
# This assumes tests are run from the project root where 'code' is a sibling
# or the script is run directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_project_structure import setup_directories, DIRECTORIES, PROJECT_ROOT

class TestProjectStructure:
    """Tests for the project structure setup."""

    def test_directories_exist(self):
        """Verify that all required directories exist after setup."""
        # Run setup to ensure directories are created
        setup_directories()
        
        # Check each required directory
        for dir_name in DIRECTORIES:
            dir_path = PROJECT_ROOT / dir_name
            assert dir_path.exists(), f"Directory missing: {dir_path}"
            assert dir_path.is_dir(), f"Not a directory: {dir_path}"

    def test_placeholder_files_exist(self):
        """Verify that placeholder files were created to mark directories."""
        setup_directories()
        
        # Check a few key placeholder files
        expected_files = [
            "src/__init__.py",
            "tests/__init__.py",
            "data/raw/.gitkeep",
            "specs/001-gene-regulation/.gitkeep",
        ]
        
        for file_name in expected_files:
            file_path = PROJECT_ROOT / file_name
            assert file_path.exists(), f"Placeholder file missing: {file_path}"
            assert file_path.is_file(), f"Not a file: {file_path}"

    def test_specs_contract_directory_exists(self):
        """Specifically check the contracts directory for schemas."""
        setup_directories()
        contracts_dir = PROJECT_ROOT / "specs/001-gene-regulation/contracts"
        assert contracts_dir.exists(), "Contracts directory missing"
        assert contracts_dir.is_dir(), "Contracts path is not a directory"