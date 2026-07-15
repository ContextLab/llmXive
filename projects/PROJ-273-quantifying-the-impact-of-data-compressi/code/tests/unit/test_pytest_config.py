"""
Tests to verify pytest configuration and environment setup.
"""
import pytest
import sys
import os

def test_pytest_timeout_plugin_available():
    """Verify pytest-timeout plugin is available."""
    import pytest_timeout
    assert pytest_timeout is not None

def test_pytest_cov_plugin_available():
    """Verify pytest-cov plugin is available."""
    import pytest_cov
    assert pytest_cov is not None

def test_code_path_injection():
    """Verify that the code path injection works."""
    code_root = Path(__file__).parent.parent.parent / "code"
    assert str(code_root) in sys.path

def test_basic_import():
    """Verify we can import the validate module."""
    from src.data.validate import validate_metadata
    assert validate_metadata is not None
