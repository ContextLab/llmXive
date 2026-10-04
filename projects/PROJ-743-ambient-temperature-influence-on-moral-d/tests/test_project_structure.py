"""
Tests for T007: Project Structure Creation.
Verifies that the required directories exist after setup.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results/figures",
    "results/logs",
    "results/stats",
    "tests"
]

@pytest.fixture(scope="module")
def project_root():
    """Return the project root path."""
    return Path.cwd()

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(project_root, dir_name):
    """Assert that each required directory exists."""
    full_path = project_root / dir_name
    assert full_path.exists(), f"Directory {full_path} does not exist."
    assert full_path.is_dir(), f"Path {full_path} exists but is not a directory."

def test_data_raw_is_writable(project_root):
    """Assert that data/raw is writable (basic check)."""
    test_file = project_root / "data/raw" / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Could not write to data/raw: {e}")

def test_results_logs_is_writable(project_root):
    """Assert that results/logs is writable (basic check)."""
    test_file = project_root / "results/logs" / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Could not write to results/logs: {e}")