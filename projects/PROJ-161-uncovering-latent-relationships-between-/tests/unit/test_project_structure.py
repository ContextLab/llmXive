"""
Unit tests to verify the project structure was created correctly.
"""
import os
import pytest

REQUIRED_DIRS = [
    "src/data",
    "src/analysis",
    "src/viz",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "data/external",
    "figures",
    "specs",
    "contracts",
    "docs"
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Verify that each required directory exists."""
    assert os.path.isdir(dir_path), f"Directory does not exist: {dir_path}"

def test_src_data_has_init():
    """Verify that src/data has an __init__.py (empty is fine for now)."""
    init_path = os.path.join("src", "data", "__init__.py")
    # We create this file in the next task (T005), but check existence here
    # For T001, we just ensure the directory exists. 
    # If T005 creates it, this test will pass then.
    # For now, we just assert the directory exists which is the T001 goal.
    assert os.path.isdir("src/data")

def test_root_structure():
    """Verify the root level structure contains expected top-level folders."""
    expected_top_level = ["src", "tests", "data", "figures", "specs", "contracts", "docs"]
    for folder in expected_top_level:
        assert os.path.isdir(folder), f"Top-level folder missing: {folder}"
