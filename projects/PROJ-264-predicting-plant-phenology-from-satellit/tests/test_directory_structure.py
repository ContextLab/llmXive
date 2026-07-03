"""
Verification that the required directory structure exists.
This test ensures T001b (and related setup tasks) have created the necessary folders.
"""
import os
from pathlib import Path

def test_tests_directory_exists():
    """Verify the root tests/ directory exists."""
    root = Path(__file__).parent.parent
    tests_dir = root / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_tests_subdirectories_exist():
    """Verify standard test subdirectories exist."""
    root = Path(__file__).parent.parent
    subdirs = ["contract", "data", "integration", "unit"]
    for subdir in subdirs:
        path = root / "tests" / subdir
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_tests_init_files_exist():
    """Verify __init__.py files exist in test directories to make them packages."""
    root = Path(__file__).parent.parent
    dirs_to_check = [
        "tests",
        "tests/contract",
        "tests/data",
        "tests/integration",
        "tests/unit"
    ]
    for d in dirs_to_check:
        path = root / d / "__init__.py"
        assert path.exists(), f"Missing __init__.py at {path}"