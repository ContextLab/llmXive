"""
Test to verify the project directory structure created by T001a.
"""
import os
import pytest
from pathlib import Path

# Determine the project root (parent of 'tests')
PROJECT_ROOT = Path(__file__).parent.parent

REQUIRED_DIRS = [
    "src",
    "tests",
    "config",
    "data",
    "results",
    "docs",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "src/pipeline",
    "src/utils",
    "src/data_models"
]

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(project_root, dir_path):
    """Verify that each required directory exists."""
    full_path = project_root / dir_path
    assert full_path.exists(), f"Directory {full_path} does not exist."
    assert full_path.is_dir(), f"Path {full_path} exists but is not a directory."

def test_structure_completeness(project_root):
    """
    Verify that the core structure is present.
    This test ensures that T001a was executed successfully.
    """
    missing = []
    for dir_name in REQUIRED_DIRS:
        if not (project_root / dir_name).exists():
            missing.append(dir_name)
    
    if missing:
        pytest.fail(f"Missing required directories: {', '.join(missing)}")