"""
Unit tests for the project structure setup.

Verifies that the required directories (src/, tests/, data/, specs/001-gene-regulation/)
are correctly created and accessible.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from setup_project_structure import setup_directories, DIRECTORIES

class TestProjectStructure:
    """
    Test suite for verifying the project directory creation logic.
    """

    def test_setup_creates_all_required_directories(self):
        """
        Verify that setup_directories creates all directories listed in DIRECTORIES.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            result = setup_directories(root)
            
            # Check that no errors occurred
            assert len(result["errors"]) == 0, f"Errors occurred: {result['errors']}"
            
            # Verify all expected directories exist
            for dir_name in DIRECTORIES:
                expected_path = root / dir_name
                assert expected_path.exists(), f"Directory {expected_path} was not created."
                assert expected_path.is_dir(), f"{expected_path} exists but is not a directory."

    def test_specific_required_paths_exist(self):
        """
        Verify the specific paths mentioned in the task description exist:
        src/, tests/, data/, specs/001-gene-regulation/
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            setup_directories(root)
            
            required_paths = [
                "src",
                "tests",
                "data",
                "specs/001-gene-regulation"
            ]
            
            for path_str in required_paths:
                full_path = root / path_str
                assert full_path.exists(), f"Required path {full_path} is missing."
                assert full_path.is_dir(), f"Required path {full_path} is not a directory."

    def test_nested_data_directories_exist(self):
        """
        Verify that nested data directories (raw, derived, gold_standard) are created.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            setup_directories(root)
            
            data_subdirs = ["data/raw", "data/derived", "data/gold_standard"]
            
            for subdir in data_subdirs:
                full_path = root / subdir
                assert full_path.exists(), f"Data subdirectory {full_path} is missing."

    def test_specs_contracts_directory_exists(self):
        """
        Verify the contracts directory under specs is created.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            setup_directories(root)
            
            contracts_path = root / "specs/001-gene-regulation/contracts"
            assert contracts_path.exists(), f"Contracts directory {contracts_path} is missing."
            assert contracts_path.is_dir(), f"{contracts_path} is not a directory."

    def test_idempotency(self):
        """
        Verify that running setup_directories twice does not cause errors.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            
            # Run once
            result1 = setup_directories(root)
            assert len(result1["errors"]) == 0
            
            # Run again
            result2 = setup_directories(root)
            assert len(result2["errors"]) == 0
            
            # Verify directories still exist
            for dir_name in DIRECTORIES:
                assert (root / dir_name).exists()
