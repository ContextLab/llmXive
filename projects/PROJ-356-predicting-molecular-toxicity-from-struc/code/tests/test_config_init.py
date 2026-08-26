"""
Tests to verify that the test package and fixtures are correctly initialized.
"""
import pytest
from pathlib import Path
import sys
import os

def test_tests_package_importable():
    """Verify the tests package can be imported."""
    try:
        import tests
        assert hasattr(tests, '__path__'), "tests is not a package"
    except ImportError as e:
        pytest.fail(f"Failed to import tests package: {e}")

def test_conftest_fixtures_available():
    """Verify that conftest fixtures are available."""
    try:
        from tests.conftest import project_root, code_dir, src_dir, test_data_dir, add_code_to_path
        # Verify types
        assert callable(project_root) or isinstance(project_root, Path)
    except ImportError as e:
        pytest.fail(f"Failed to import fixtures from conftest: {e}")
