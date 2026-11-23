"""
Example integration test to verify the framework setup.
This test checks basic project structure and imports.
"""
import pytest
from pathlib import Path

def test_code_directory_exists(project_root):
    """Verify that the code directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Code directory missing: {code_dir}"
    assert code_dir.is_dir(), f"Code path is not a directory: {code_dir}"

def test_data_directory_exists(project_root):
    """Verify that the data directory exists."""
    data_dir = project_root / "data"
    assert data_dir.exists(), f"Data directory missing: {data_dir}"
    assert data_dir.is_dir(), f"Data path is not a directory: {data_dir}"

def test_import_utils(project_root):
    """Verify that we can import from the utils module."""
    try:
        from utils import get_logger
        assert get_logger is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from utils: {e}")
