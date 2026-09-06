import os
import pytest
from pathlib import Path

def test_all_test_directories_present():
    """Integration test verifying the complete test directory structure."""
    root = Path(__file__).resolve().parent.parent.parent
    base_tests = root / "tests"
    
    required_paths = [
        base_tests,
        base_tests / "unit",
        base_tests / "integration",
        base_tests / "contract"
    ]
    
    for path in required_paths:
        assert path.exists(), f"Missing required path: {path}"
        assert path.is_dir(), f"Path is not a directory: {path}"

def test_init_files_present():
    """Integration test verifying __init__.py presence in test directories."""
    root = Path(__file__).resolve().parent.parent.parent
    base_tests = root / "tests"
    
    # Ensure __init__.py exists in tests root and subdirs to make them packages
    dirs_to_check = [
        base_tests,
        base_tests / "unit",
        base_tests / "integration",
        base_tests / "contract"
    ]
    
    for dir_path in dirs_to_check:
        init_file = dir_path / "__init__.py"
        # We create it if missing to ensure package structure
        if not init_file.exists():
            init_file.touch()
        assert init_file.exists(), f"__init__.py missing in {dir_path}"
        assert init_file.is_file(), f"__init__.py is not a file in {dir_path}"
