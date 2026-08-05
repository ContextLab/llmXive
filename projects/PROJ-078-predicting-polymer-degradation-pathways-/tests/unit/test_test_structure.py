"""
Basic test to verify the pytest framework is correctly configured.
This test should pass if T008 is successfully implemented.
"""
import pytest
import sys
from pathlib import Path

def test_pytest_is_running():
    """Verify that pytest is the test runner."""
    assert True

def test_code_importable():
    """Verify that the code directory is importable."""
    try:
        # Attempt to import a known module from the code directory
        # This verifies the conftest.py path injection is working
        import utils
        assert utils is not None
    except ImportError as e:
        pytest.fail(f"Failed to import utils module: {e}")

def test_project_paths_accessible():
    """Verify that project paths can be resolved."""
    from utils import get_project_paths
    paths = get_project_paths()
    assert paths is not None
    assert hasattr(paths, 'code_dir') or 'code' in str(paths)
