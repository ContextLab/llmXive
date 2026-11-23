import os
from pathlib import Path
import pytest
from code.setup_dirs import (
    create_data_directories,
    create_test_directories,
    create_source_directories,
    create_all_directories
)

def test_create_source_directories():
    """Test that the code directory is created."""
    create_source_directories()
    assert Path("code").is_dir(), "code/ directory should exist"

def test_create_data_directories():
    """Test that data subdirectories are created."""
    create_data_directories()
    assert Path("data/raw").is_dir(), "data/raw should exist"
    assert Path("data/interim").is_dir(), "data/interim should exist"
    assert Path("data/results").is_dir(), "data/results should exist"

def test_create_test_directories():
    """Test that test subdirectories are created."""
    create_test_directories()
    assert Path("tests/unit").is_dir(), "tests/unit should exist"
    assert Path("tests/integration").is_dir(), "tests/integration should exist"

def test_create_all_directories():
    """Test the full directory creation workflow."""
    # Clean up first to ensure we are testing creation
    for p in ["code", "data", "tests", "docs"]:
        if Path(p).exists():
            import shutil
            shutil.rmtree(p)
    
    create_all_directories()
    
    assert Path("code").is_dir()
    assert Path("data/raw").is_dir()
    assert Path("data/interim").is_dir()
    assert Path("data/results").is_dir()
    assert Path("tests/unit").is_dir()
    assert Path("tests/integration").is_dir()
    assert Path("docs").is_dir()