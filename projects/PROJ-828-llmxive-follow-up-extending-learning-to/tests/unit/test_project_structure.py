"""
Unit tests to verify the project directory structure has been created correctly.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/training",
    "code/analysis",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "results",
    "results/opd",
    "results/low_rank_rl",
    "results/analysis",
    "figures",
    "specs",
    "state",
]

@pytest.fixture(scope="module")
def project_root():
    """Returns the root directory of the project."""
    return Path(".")

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(project_root, dir_name):
    """Test that each required directory exists."""
    full_path = project_root / dir_name
    assert full_path.exists(), f"Directory {full_path} does not exist."
    assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_init_files_exist(project_root):
    """Test that __init__.py files exist for Python packages."""
    package_dirs = [
        "code", "code/utils", "code/data", "code/models", 
        "code/training", "code/analysis", "tests", "tests/unit", "tests/integration"
    ]
    for pkg_dir in package_dirs:
        init_file = project_root / pkg_dir / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {pkg_dir}"