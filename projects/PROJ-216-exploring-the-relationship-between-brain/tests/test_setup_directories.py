import os
import pytest
from pathlib import Path
from code.setup_directories import create_directories, create_init_files

def test_create_directories():
    """Test that the required directory structure is created."""
    created = create_directories()
    
    required_dirs = [
        "data/raw",
        "data/interim",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "reports",
        "figures",
        "logs",
    ]
    
    for rel_path in required_dirs:
        path = Path(rel_path)
        assert path.exists(), f"Directory {rel_path} was not created"
        assert path.is_dir(), f"{rel_path} exists but is not a directory"

def test_create_init_files():
    """Test that __init__.py files are created."""
    created = create_init_files()
    
    required_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for rel_path in required_files:
        path = Path(rel_path)
        assert path.exists(), f"File {rel_path} was not created"
        assert path.is_file(), f"{rel_path} exists but is not a file"

def test_reports_directory_exists():
    """Specific test for T001e: Reports directory must exist."""
    reports_path = Path("reports")
    assert reports_path.exists(), "Reports directory does not exist"
    assert reports_path.is_dir(), "Reports path is not a directory"
    
    # Ensure there is at least a .gitkeep or placeholder to prove it's not empty
    # (Optional, but good for verification)
    # We rely on the create_directories/main logic to ensure this, 
    # but checking existence is the primary requirement.