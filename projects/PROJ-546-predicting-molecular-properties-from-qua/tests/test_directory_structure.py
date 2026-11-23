"""
Unit tests for T001: Verify that the project directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to import create_directories
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.create_directories import create_directories

def test_directory_structure_exists(tmp_path):
    """Test that all required directories are created."""
    create_directories(tmp_path)
    
    required_dirs = [
        "code",
        "data/raw",
        "data/optimized_geometries",
        "logs",
        "reports",
        "specs/546-predicting-molecular-properties/contracts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    for dir_name in required_dirs:
        dir_path = tmp_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_test_packages_have_init(tmp_path):
    """Test that test subdirectories have __init__.py files."""
    create_directories(tmp_path)
    
    test_subdirs = ["tests/unit", "tests/integration", "tests/contract"]
    
    for subdir in test_subdirs:
        init_path = tmp_path / subdir / "__init__.py"
        assert init_path.exists(), f"__init__.py missing in {subdir}"

def test_nested_structure(tmp_path):
    """Test that nested directories are created with parents=True."""
    create_directories(tmp_path)
    
    # Verify deeply nested directory
    nested = tmp_path / "specs" / "546-predicting-molecular-properties" / "contracts"
    assert nested.exists()
    assert nested.is_dir()
