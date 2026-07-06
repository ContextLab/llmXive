"""
Unit tests to verify the project directory structure was created correctly.
"""
import os
import pytest
import sys

# Add the parent directory to the path to import setup script logic if needed,
# though we primarily test the filesystem state.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REQUIRED_DIRS = [
    "code",
    "code/extraction",
    "code/inference",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/extracted",
    "data/aggregated",
    "data/results",
    "data/models",
    "tests/unit",
    "tests/integration"
]

@pytest.fixture(scope="module")
def base_path():
    return project_root

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(base_path, dir_name):
    """Assert that each required directory exists."""
    full_path = os.path.join(base_path, dir_name)
    assert os.path.isdir(full_path), f"Directory {dir_name} does not exist at {full_path}"

def test_code_subdirs_exist(base_path):
    """Assert specific subdirectories under code/ exist."""
    code_subdirs = ["extraction", "inference", "analysis", "utils"]
    for subdir in code_subdirs:
        path = os.path.join(base_path, "code", subdir)
        assert os.path.isdir(path), f"Subdirectory code/{subdir} is missing"

def test_data_subdirs_exist(base_path):
    """Assert specific subdirectories under data/ exist."""
    data_subdirs = ["raw", "extracted", "aggregated", "results", "models"]
    for subdir in data_subdirs:
        path = os.path.join(base_path, "data", subdir)
        assert os.path.isdir(path), f"Subdirectory data/{subdir} is missing"

def test_tests_subdirs_exist(base_path):
    """Assert specific subdirectories under tests/ exist."""
    tests_subdirs = ["unit", "integration"]
    for subdir in tests_subdirs:
        path = os.path.join(base_path, "tests", subdir)
        assert os.path.isdir(path), f"Subdirectory tests/{subdir} is missing"