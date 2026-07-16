"""
Pytest configuration and fixtures for the project.
"""
import os
import pytest


@pytest.fixture(scope="session")
def project_root():
    """Return the root directory of the project."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))