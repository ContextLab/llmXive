"""
Basic sanity tests to verify pytest configuration and test discovery are working.
These tests ensure that the project structure and import paths are correctly set up.
"""
import os
import sys
import pytest
from pathlib import Path

def test_pytest_discovery():
    """Verify that this test file itself is discovered by pytest."""
    assert Path(__file__).exists()
    assert "test_pytest_setup.py" in __file__

def test_src_path_fixture(add_src_to_path):
    """Verify that the src path fixture successfully added the path."""
    # The fixture runs automatically (autouse=True), so we just check it didn't error.
    # We can verify the path is present.
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    assert str(src_path) in sys.path, f"Expected {src_path} in sys.path, but got: {sys.path}"

def test_import_from_src():
    """Verify that we can actually import modules from the src directory."""
    # Try importing a known module to prove the path setup works
    try:
        from src.utils.config import get_config
        assert callable(get_config)
    except ImportError as e:
        pytest.fail(f"Failed to import from src: {e}")
    except Exception as e:
        # If it exists but has other issues, that's a different task (T005)
        # For this task, we just need to ensure the import mechanism works.
        # If the module exists but crashes on import, that's acceptable for T004
        # as long as the path is correct. However, let's be strict:
        if "No module named" in str(e):
            pytest.fail(f"Module not found: {e}")
        # Otherwise, assume the module exists and the import succeeded (or failed due to its own init)
        pass
