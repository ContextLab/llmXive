"""
Basic test to verify pytest configuration is working correctly.
"""
import pytest
from pathlib import Path

def test_pytest_imports():
    """Verify pytest can import standard modules."""
    assert pytest is not None

def test_path_resolution(project_root):
    """Verify project root path is correctly resolved."""
    assert project_root.exists()
    assert isinstance(project_root, Path)

def test_directory_structure(project_root):
    """Verify required test directories exist."""
    assert (project_root / "tests" / "unit").exists()
    assert (project_root / "tests" / "integration").exists()
    assert (project_root / "tests" / "contract").exists()

def test_conftest_fixtures(project_root, data_dir, code_dir, tests_dir):
    """Verify fixtures from conftest.py are available."""
    assert data_dir.exists()
    assert code_dir.exists()
    assert tests_dir.exists()
    assert data_dir.parent == project_root
    assert code_dir.parent == project_root
    assert tests_dir.parent == project_root