import os
import pytest
from pathlib import Path
import shutil
import tempfile
from setup_structure import create_project_structure, ensure_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        yield root
        # Cleanup is handled by TemporaryDirectory context manager

def test_create_project_structure_creates_directories(temp_project_root):
    """Test that all required directories are created."""
    required_dirs = [
        "code",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests",
        "state",
        "docs",
        "logs",
        "figures",
    ]
    
    create_project_structure(temp_project_root)
    
    for dir_name in required_dirs:
        dir_path = temp_project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} was not created"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_create_project_structure_creates_submodules(temp_project_root):
    """Test that specific code subdirectories exist."""
    create_project_structure(temp_project_root)
    
    code_subdirs = ["data", "preprocess", "analysis", "modeling", "validation", "report", "utils"]
    for subdir in code_subdirs:
        dir_path = temp_project_root / "code" / subdir
        assert dir_path.exists(), f"Code submodule {subdir} was not created"

def test_ensure_init_files_creates_init(temp_project_root):
    """Test that __init__.py files are created."""
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    init_dirs = ["code", "code/data", "code/analysis", "code/modeling", "tests"]
    for dir_name in init_dirs:
        init_file = temp_project_root / dir_name / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_name}"

def test_idempotency(temp_project_root):
    """Test that running the setup multiple times doesn't cause errors."""
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Run again
    create_project_structure(temp_project_root)
    ensure_init_files(temp_project_root)
    
    # Verify structure still exists
    assert (temp_project_root / "code").exists()
    assert (temp_project_root / "data/raw").exists()
    assert (temp_project_root / "code" / "__init__.py").exists()