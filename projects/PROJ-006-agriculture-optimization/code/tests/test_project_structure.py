"""
Test to verify that the project structure has been created correctly.
This test validates T001 implementation.
"""
import os
import pytest
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def test_required_directories_exist():
    """Verify all required directories from T001 exist."""
    root = get_project_root()
    
    required_dirs = [
        "code/src",
        "code/tests",
        "code/contracts",
        "code/data",
        "code/src/cli",
        "code/src/config",
        "code/src/data/collectors",
        "code/src/data/generators",
        "code/src/data/processing",
        "code/src/utils",
        "code/src/analysis",
        "code/src/services",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        "code/data/raw",
        "code/data/processed",
        "code/data/logs",
        "code/data/remote_sensing",
        "code/scripts",
        "code/figures",
        "code/reports",
        "docs",
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        pytest.fail(f"Missing required directories: {', '.join(missing)}")

def test_structure_is_writable():
    """Verify we can write to the data directories."""
    root = get_project_root()
    test_file = root / "code" / "data" / "processed" / ".test_write"
    
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Cannot write to data/processed: {e}")
