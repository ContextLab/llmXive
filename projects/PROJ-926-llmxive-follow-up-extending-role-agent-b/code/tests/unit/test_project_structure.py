import os
import pytest
import tempfile
import shutil
from pathlib import Path
from setup_project_structure import create_project_structure

def get_base_dir():
    """Helper to determine the base directory for the test."""
    # Since we are running from code/tests/unit, the project root is 3 levels up
    return Path(__file__).resolve().parent.parent.parent.parent

def test_required_directories_exist():
    """Verify that the core directories src, tests, data, state, docs exist."""
    base_dir = get_base_dir()
    required = ["src", "tests", "data", "state", "docs"]
    for d in required:
        assert (base_dir / d).exists(), f"Directory {d} is missing"

def test_src_directory_exists():
    """Verify src subdirectories exist."""
    base_dir = get_base_dir()
    src_dirs = [
        "src/config", "src/sim", "src/retrieval", 
        "src/conditions", "src/analysis", 
        "src/data/raw", "src/data/derived"
    ]
    for d in src_dirs:
        assert (base_dir / d).exists(), f"Source directory {d} is missing"

def test_tests_directory_exists():
    """Verify tests subdirectories exist."""
    base_dir = get_base_dir()
    test_dirs = [
        "tests/contract", "tests/integration", "tests/unit"
    ]
    for d in test_dirs:
        assert (base_dir / d).exists(), f"Test directory {d} is missing"

def test_data_directory_exists():
    """Verify data subdirectories exist."""
    base_dir = get_base_dir()
    data_dirs = [
        "data/raw", "data/derived"
    ]
    for d in data_dirs:
        assert (base_dir / d).exists(), f"Data directory {d} is missing"

def test_nested_structure_valid():
    """Comprehensive check of the entire required structure."""
    base_dir = get_base_dir()
    all_paths = [
        "src/config", "src/sim", "src/retrieval", "src/conditions", "src/analysis",
        "src/data/raw", "src/data/derived",
        "tests/contract", "tests/integration", "tests/unit",
        "data/raw", "data/derived", "state", "docs"
    ]
    missing = []
    for p in all_paths:
        if not (base_dir / p).exists():
            missing.append(p)
    
    assert len(missing) == 0, f"The following directories are missing: {missing}"