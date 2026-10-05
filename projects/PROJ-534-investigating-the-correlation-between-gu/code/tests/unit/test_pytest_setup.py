"""
Unit tests to verify the pytest configuration and directory structure.
"""
import pytest
import os
from pathlib import Path

def test_project_root_accessible(project_root):
    """Verify that the project root fixture returns a valid Path."""
    assert isinstance(project_root, Path)
    assert project_root.exists()
    # Check for expected subdirectories
    assert (project_root / "src").exists(), "src directory missing"
    assert (project_root / "tests").exists(), "tests directory missing"
    assert (project_root / "data").exists(), "data directory missing"

def test_required_directories_exist(project_root):
    """Verify that required data directories exist or can be created."""
    data_dirs = ["raw", "processed", "results"]
    for d in data_dirs:
        dir_path = project_root / "data" / d
        assert dir_path.exists() or dir_path.mkdir(parents=True, exist_ok=True), \
            f"Could not ensure existence of {dir_path}"

def test_imports_from_src_work(project_root):
    """Verify that imports from the src module work correctly."""
    try:
        # Attempt to import a known module from the config
        from code.src.utils.config import get_project_root
        assert callable(get_project_root)
    except ImportError as e:
        pytest.fail(f"Import from src failed: {e}")
