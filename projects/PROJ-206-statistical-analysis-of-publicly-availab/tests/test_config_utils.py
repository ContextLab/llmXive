"""
Tests for the configuration utilities.
"""
import pytest
from pathlib import Path

# Import from the code directory structure
# Note: We assume the code directory is in the path via conftest.py
try:
    from src.utils.config import get_project_root, get_data_root, get_state_root, get_code_root
except ImportError:
    pytest.skip("Configuration utilities not yet implemented", allow_module_level=True)

def test_get_project_root():
    """
    Verify that get_project_root returns the correct root directory.
    """
    root = get_project_root()
    assert root.exists(), "Project root does not exist"
    assert root.is_dir(), "Project root is not a directory"

def test_get_code_root():
    """
    Verify that get_code_root returns the code directory.
    """
    code_root = get_code_root()
    assert code_root.exists(), "Code root does not exist"
    assert code_root.is_dir(), "Code root is not a directory"
    assert code_root.name == "code", f"Expected 'code' directory, got '{code_root.name}'"