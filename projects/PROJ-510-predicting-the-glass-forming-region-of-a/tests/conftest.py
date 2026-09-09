"""
Pytest configuration and fixtures for the test suite.
"""
import pytest
import os
import sys

# Add the project root to the path so imports work
@pytest.fixture(scope="session", autouse=True)
def add_project_root():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    yield
    # Cleanup if necessary
