"""
Basic sanity checks for the pytest configuration and directory structure.
"""
import pytest
import os
from pathlib import Path

def test_project_root_accessible():
    """Verify that the project root is accessible from tests."""
    # The test runner should be invoked from the 'code' directory
    # or the PYTHONPATH should be set such that 'code' is importable.
    project_root = Path(__file__).parent.parent.parent
    assert project_root.exists(), "Project root directory does not exist"
    assert (project_root / "pytest.ini").exists(), "pytest.ini not found in project root"

def test_required_directories_exist():
    """Verify that the required test directory structure exists."""
    base = Path(__file__).parent.parent
    required_dirs = [
        "unit",
        "integration",
        "contract"
    ]
    for d in required_dirs:
        dir_path = base / d
        assert dir_path.exists(), f"Directory {d} missing in tests/"
        assert (dir_path / "__init__.py").exists(), f"Missing __init__.py in {d}/"

def test_imports_from_src_work():
    """Verify that imports from src modules work correctly."""
    try:
        from code.src.utils.config import get_project_root
        from code.src.data.filtering import filter_cohort
        from code.src.analysis.correlation import calculate_skewness
    except ImportError as e:
        pytest.fail(f"Failed to import from src modules: {e}")