import os
import pytest
from pathlib import Path

# Determine project root relative to this test file
# File is at code/tests/test_project_structure.py -> root is parent of 'code'
TEST_FILE_DIR = Path(__file__).resolve().parent
CODE_DIR = TEST_FILE_DIR
PROJECT_ROOT = CODE_DIR.parent

def test_required_directories_exist():
    """Verify top-level required directories exist."""
    required_dirs = ["src", "tests", "contracts", "state"]
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_nested_data_directories_exist():
    """Verify nested data directories exist."""
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/profiling"
    ]
    for dir_name in data_dirs:
        dir_path = PROJECT_ROOT / dir_name
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"