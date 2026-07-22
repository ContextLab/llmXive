"""
Tests for T001a: Project directory structure creation.

Verifies that the required directory tree exists after running the creation script.
"""
import os
import pytest
from pathlib import Path
import shutil

PROJECT_NAME = "PROJ-379-predicting-molecular-excitation-waveleng"
BASE_DIR = Path("projects") / PROJECT_NAME

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Ensure clean state before and after tests."""
    # Setup: Ensure base dir exists for the test to work against (or clean it if it exists)
    # Note: In a real CI environment, this might be handled by the runner.
    # We assume the create script has been run or will be run.
    yield
    # Teardown: Optional cleanup if needed, but often we leave artifacts for verification
    # if os.path.exists(BASE_DIR):
    #     shutil.rmtree(BASE_DIR)

def test_project_root_exists():
    """Verify the project root directory exists."""
    assert BASE_DIR.exists(), f"Project root {BASE_DIR} does not exist."
    assert BASE_DIR.is_dir(), f"{BASE_DIR} is not a directory."

def test_data_raw_exists():
    """Verify data/raw directory exists."""
    path = BASE_DIR / "data" / "raw"
    assert path.exists(), f"Directory {path} does not exist."
    assert path.is_dir(), f"{path} is not a directory."

def test_data_processed_exists():
    """Verify data/processed directory exists."""
    path = BASE_DIR / "data" / "processed"
    assert path.exists(), f"Directory {path} does not exist."
    assert path.is_dir(), f"{path} is not a directory."

def test_code_dir_exists():
    """Verify code directory exists."""
    path = BASE_DIR / "code"
    assert path.exists(), f"Directory {path} does not exist."
    assert path.is_dir(), f"{path} is not a directory."

def test_tests_dir_exists():
    """Verify tests directory exists."""
    path = BASE_DIR / "tests"
    assert path.exists(), f"Directory {path} does not exist."
    assert path.is_dir(), f"{path} is not a directory."

def test_docs_dir_exists():
    """Verify docs directory exists."""
    path = BASE_DIR / "docs"
    assert path.exists(), f"Directory {path} does not exist."
    assert path.is_dir(), f"{path} is not a directory."

def test_directory_structure_complete():
    """Verify the entire expected structure is present."""
    expected_paths = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    for rel_path in expected_paths:
        full_path = BASE_DIR / rel_path
        assert full_path.exists(), f"Missing expected directory: {full_path}"
        assert full_path.is_dir(), f"Expected directory but found file: {full_path}"