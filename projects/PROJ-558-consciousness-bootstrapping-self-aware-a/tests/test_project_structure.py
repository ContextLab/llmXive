"""
Test suite to verify the project directory structure created by T001a.
"""
import os
import pytest
from pathlib import Path

# We assume the script has been run and the structure exists relative to the test root
# or we check the current working directory if the test is run from there.
# For robustness, we check relative to the file location if needed, but typically
# these tests run from the project root.

PROJECT_NAME = "PROJ-558-consciousness-bootstrapping-self-aware-a"
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "artifacts/checkpoints",
    "artifacts/results",
]

def get_project_root():
    """
    Attempts to locate the project root directory.
    Checks current working directory first, then parent directories.
    """
    current = Path.cwd()
    # Check if we are already in the project root or a subdirectory
    if (current / "projects" / PROJECT_NAME).exists():
        return current / "projects" / PROJECT_NAME
    
    # Check parents
    for parent in current.parents:
        potential_root = parent / "projects" / PROJECT_NAME
        if potential_root.exists():
            return potential_root
    
    # If not found, assume current dir is the root (for local dev scenarios)
    # and look for the project folder there or just return current if structure is flat
    # But the spec says "projects/..." so we enforce that.
    # If running from the code directory, we need to go up.
    # Let's assume the test is run from the repository root.
    return Path.cwd() / "projects" / PROJECT_NAME

def test_project_directory_exists():
    """
    T001a: Verify the main project directory exists.
    """
    root = get_project_root()
    assert root.exists(), f"Project root directory does not exist: {root}"
    assert root.is_dir(), f"Project root is not a directory: {root}"

@pytest.mark.parametrize("subdir", REQUIRED_DIRS)
def test_required_subdirectory_exists(subdir):
    """
    T001a: Verify each required subdirectory exists.
    """
    root = get_project_root()
    dir_path = root / subdir
    assert dir_path.exists(), f"Required subdirectory missing: {dir_path}"
    assert dir_path.is_dir(), f"Required subdirectory is not a directory: {dir_path}"

def test_artifacts_checkpoints_exists():
    """
    T001a: Specifically verify artifacts/checkpoints exists.
    """
    root = get_project_root()
    checkpoints = root / "artifacts" / "checkpoints"
    assert checkpoints.exists(), f"Missing: {checkpoints}"
    assert checkpoints.is_dir(), f"Not a directory: {checkpoints}"

def test_artifacts_results_exists():
    """
    T001a: Specifically verify artifacts/results exists.
    """
    root = get_project_root()
    results = root / "artifacts" / "results"
    assert results.exists(), f"Missing: {results}"
    assert results.is_dir(), f"Not a directory: {results}"

def test_data_raw_exists():
    """
    T001a: Specifically verify data/raw exists.
    """
    root = get_project_root()
    raw = root / "data" / "raw"
    assert raw.exists(), f"Missing: {raw}"
    assert raw.is_dir(), f"Not a directory: {raw}"

def test_data_processed_exists():
    """
    T001a: Specifically verify data/processed exists.
    """
    root = get_project_root()
    processed = root / "data" / "processed"
    assert processed.exists(), f"Missing: {processed}"
    assert processed.is_dir(), f"Not a directory: {processed}"