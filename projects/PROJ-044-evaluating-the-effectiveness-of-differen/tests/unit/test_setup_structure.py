"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest

REQUIRED_DIRECTORIES = [
    "code/data",
    "code/training",
    "code/analysis",
    "code/models",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/partitions",
    "results",
    "artifacts"
]

@pytest.fixture(scope="module")
def project_root():
    # Assuming tests are run from the project root
    return os.getcwd()

@pytest.mark.parametrize("dir_path", REQUIRED_DIRECTORIES)
def test_directory_exists(project_root, dir_path):
    """Test that each required directory exists."""
    full_path = os.path.join(project_root, dir_path)
    assert os.path.exists(full_path), f"Directory {dir_path} does not exist"
    assert os.path.isdir(full_path), f"{dir_path} exists but is not a directory"

def test_all_directories_exist(project_root):
    """Test that all required directories exist in one go."""
    missing_dirs = []
    for dir_path in REQUIRED_DIRECTORIES:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            missing_dirs.append(dir_path)
    
    assert len(missing_dirs) == 0, f"Missing directories: {missing_dirs}"