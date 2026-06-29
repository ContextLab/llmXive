"""
Test for T001c - Verify project directory structure exists.

This test ensures all required directories were created by setup_directories.py.
"""
import os
import pytest
from pathlib import Path

# Get the project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_DIRS = [
    "data",
    "data/raw",
    "data/derived",
    "data/samples",
    "results",
    "results/shap_plots",
    "logs",
    "state",
    "contracts",
]

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(project_root, dir_name):
    """Verify each required directory exists under project root."""
    full_path = project_root / dir_name
    assert full_path.exists(), f"Directory {dir_name} does not exist"
    assert full_path.is_dir(), f"{dir_name} is not a directory"

def test_data_subdirectories(project_root):
    """Verify all data subdirectories exist."""
    data_dirs = ["raw", "derived", "samples"]
    for subdir in data_dirs:
        path = project_root / "data" / subdir
        assert path.exists(), f"data/{subdir} does not exist"
        assert path.is_dir(), f"data/{subdir} is not a directory"

def test_results_subdirectories(project_root):
    """Verify all results subdirectories exist."""
    results_dirs = ["shap_plots"]
    for subdir in results_dirs:
        path = project_root / "results" / subdir
        assert path.exists(), f"results/{subdir} does not exist"
        assert path.is_dir(), f"results/{subdir} is not a directory"
