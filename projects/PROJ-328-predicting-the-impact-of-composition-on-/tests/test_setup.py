"""
Integration test to verify the project directory structure setup (T001a).
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path if necessary
# Assuming this test is run from the project root
PROJECT_ROOT = Path(__file__).parent.parent

def test_data_directories_exist():
    """Verify data/raw, data/processed, and data/outputs exist."""
    data_dirs = ["data/raw", "data/processed", "data/outputs"]
    for dir_name in data_dirs:
        full_path = PROJECT_ROOT / dir_name
        assert full_path.exists(), f"Directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} is not a directory."

def test_code_directories_exist():
    """Verify all code subdirectories exist."""
    code_dirs = [
        "code/ingestion", "code/features", "code/models",
        "code/evaluation", "code/visualization", "code/utils"
    ]
    for dir_name in code_dirs:
        full_path = PROJECT_ROOT / dir_name
        assert full_path.exists(), f"Directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} is not a directory."
        # Check for __init__.py
        init_file = full_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {full_path}"

def test_tests_directories_exist():
    """Verify tests/contract and tests/integration exist."""
    test_dirs = ["tests/contract", "tests/integration"]
    for dir_name in test_dirs:
        full_path = PROJECT_ROOT / dir_name
        assert full_path.exists(), f"Directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} is not a directory."
        # Check for __init__.py
        init_file = full_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {full_path}"

def test_directory_structure_matches_spec():
    """
    Comprehensive check that the directory structure matches the T001a specification.
    """
    expected_structure = {
        "data": ["raw", "processed", "outputs"],
        "code": ["ingestion", "features", "models", "evaluation", "visualization", "utils"],
        "tests": ["contract", "integration"]
    }

    for parent, children in expected_structure.items():
        parent_path = PROJECT_ROOT / parent
        assert parent_path.exists(), f"Parent directory {parent_path} missing."
        
        for child in children:
            child_path = parent_path / child
            assert child_path.exists(), f"Child directory {child_path} missing."
            assert child_path.is_dir(), f"{child_path} is not a directory."