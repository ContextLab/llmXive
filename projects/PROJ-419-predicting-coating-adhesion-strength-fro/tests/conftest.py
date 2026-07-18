"""
Pytest configuration and shared fixtures.

This file configures pytest and provides common fixtures for tests.
"""
import os
import sys
import pytest

# Ensure the code directory is in the Python path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for all tests."""
    code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    # Cleanup not strictly necessary as sys.path is process-local,
    # but good practice in some contexts.

def pytest_configure(config):
    """Configure pytest markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
