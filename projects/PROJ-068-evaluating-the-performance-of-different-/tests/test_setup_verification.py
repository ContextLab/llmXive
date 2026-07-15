import os
import pytest
from pathlib import Path

# Determine project root relative to test file
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/processed",
    "results",
    "results/benchmarks",
    "figures",
    "specs"
]

def test_project_structure_exists():
    """
    Verify that the project directory structure required by T001 exists.
    This test ensures:
    1. All top-level directories (code, tests, data, results) exist.
    2. Required subdirectories (data/processed, results/benchmarks) exist.
    3. All paths are actual directories.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_name} (not a directory)")

    assert len(missing_dirs) == 0, f"Missing or invalid directories: {missing_dirs}"

def test_data_processed_directory():
    """Specific check for data/processed as per T007 requirement."""
    data_processed = PROJECT_ROOT / "data" / "processed"
    assert data_processed.exists(), "data/processed directory is missing"
    assert data_processed.is_dir(), "data/processed is not a directory"

def test_results_benchmarks_directory():
    """Specific check for results/benchmarks as per T023/T035 requirement."""
    results_benchmarks = PROJECT_ROOT / "results" / "benchmarks"
    assert results_benchmarks.exists(), "results/benchmarks directory is missing"
    assert results_benchmarks.is_dir(), "results/benchmarks is not a directory"
