"""
Unit test to verify that the project structure has been correctly initialized.
This test ensures that all required directories exist after running setup_project.py.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code/ingestion",
    "code/modeling",
    "code/visualization",
    "code/utils",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "data/raw",
    "data/processed",
    "docs",
]

@pytest.fixture(scope="module")
def project_root():
    """Return the current working directory as the project root."""
    return os.getcwd()

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(project_root, dir_path):
    """Verify that each required directory exists in the project structure."""
    full_path = os.path.join(project_root, dir_path)
    assert os.path.isdir(full_path), f"Directory {dir_path} does not exist at {full_path}"

def test_all_directories_created(project_root):
    """Verify that all required directories are present."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.isdir(full_path):
            missing.append(dir_path)
    
    assert not missing, f"The following directories are missing: {missing}"